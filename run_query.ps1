<#
.SYNOPSIS
    A graphical user interface to prepare commands for a remote data processing session.
.DESCRIPTION
    This script provides multiple workflows: 'Create & Process', 'Query & Download', 'Download Only', and 'Monthly Partitioned Job'.
    It uses a guided, multi-step process and automatically launches the SSH terminal for the user.
    The launched terminal will automatically close when the remote process completes.
    Python scripts are sourced from a central remote location, and user-specific files are stored in a dedicated user directory on the server.
    The script now controls window placement, validates user input, and adjusts the UI for a better user experience.
.AUTHOR
    Gemini
.VERSION
    8.7 - Fixed UI bug in Monthly Job workflow
        - Schema, Table Name, and Email fields now remain enabled for monthly jobs.
        - Refined UI state management for better user experience.
#>

# Load necessary .NET assemblies for the GUI
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Collections

# --- Win32 API for moving the terminal window ---
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
}
"@ -PassThru | Out-Null

# --- SCRIPT-LEVEL VARIABLES for State Management ---
$script:currentLogFile = ""
$script:form = New-Object System.Windows.Forms.Form
$script:sharedConfig = $null # To hold config between steps
$script:remoteCsvFullPath = "" # To hold remote file path for download

# --- HELPER FUNCTIONS ---
function Write-Log {
    param([string]$Message, [string]$Detail, [switch]$IsError)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logPrefix = if ($IsError) { "[ERROR]" } else { "[INFO]" }
    $logMessage = "$timestamp $logPrefix $Message"
    if (-not [string]::IsNullOrEmpty($script:currentLogFile)) {
        Add-Content -Path $script:currentLogFile -Value $logMessage
        if ($Detail) { Add-Content -Path $script:currentLogFile -Value $Detail }
    }
    
    $foundStatusBox = $script:form.Controls.Find("statusBox", $true)
    if ($foundStatusBox.Count -gt 0) {
        $statusBox = $foundStatusBox[0]
        $statusBox.AppendText($logMessage + "`r`n")
        if ($Detail) {
             $statusBox.AppendText($Detail + "`r`n")
        }
    }
}

function Start-ProcessAndMoveWindow {
    param([string]$ProcessName, [string]$FilePath, [string]$ArgumentList, [int]$X, [int]$Y)
    
    try {
        $initialPIDs = (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue).Id
        Start-Process -FilePath $FilePath -ArgumentList $ArgumentList
        $newProcess = $null
        for ($i = 0; $i -lt 10; $i++) {
            Start-Sleep -Milliseconds 300
            $currentPIDs = (Get-Process -Name $ProcessName -ErrorAction SilentlyContinue).Id
            $newPID = $currentPIDs | Where-Object { $initialPIDs -notcontains $_ }
            if ($newPID) {
                $newProcess = Get-Process -Id $newPID -ErrorAction SilentlyContinue
                if ($newProcess -and $newProcess.MainWindowHandle -ne [IntPtr]::Zero) { break }
            }
        }

        if ($newProcess -and $newProcess.MainWindowHandle -ne [IntPtr]::Zero) {
            $hWnd = $newProcess.MainWindowHandle
            [Win32]::SetWindowPos($hWnd, [IntPtr]::Zero, $X, $Y, 0, 0, 0x0001 -bor 0x0004) | Out-Null
        } else {
            Write-Log "Could not find the main window handle for the new process '$ProcessName'."
        }
    } catch {
        Write-Log "Failed to start or move the process window: $($_.Exception.Message)" -IsError
    }
}

# --- 1. CONSTRUCT THE GUI ---
$script:form.Text = "Impala Process Launcher v3.2"
$script:form.Size = New-Object System.Drawing.Size(640, 840); $script:form.MinimumSize = $script:form.Size; $script:form.MaximumSize = $script:form.Size
$script:form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedSingle; $script:form.StartPosition = "Manual"; $script:form.MaximizeBox = $false
$defaultFont = New-Object System.Drawing.Font("Segoe UI", 9); $script:form.Font = $defaultFont
$controls = @{} 

$gbMode = New-Object System.Windows.Forms.GroupBox; $gbMode.Text = "1. Select Operation Mode"; $gbMode.Location = New-Object System.Drawing.Point(15, 15); $gbMode.Size = New-Object System.Drawing.Size(590, 60)
$controls["radioCreate"] = New-Object System.Windows.Forms.RadioButton; $controls["radioCreate"].Text = "Create or Query from SQL file"; $controls["radioCreate"].Location = New-Object System.Drawing.Point(20, 25); $controls["radioCreate"].Size = New-Object System.Drawing.Size(250, 20); $controls["radioCreate"].Checked = $true 
$controls["radioDownload"] = New-Object System.Windows.Forms.RadioButton; $controls["radioDownload"].Text = "Download Existing Table"; $controls["radioDownload"].Location = New-Object System.Drawing.Point(280, 25); $controls["radioDownload"].Size = New-Object System.Drawing.Size(250, 20)
$gbMode.Controls.AddRange(@($controls["radioCreate"], $controls["radioDownload"]))

$gbConfig = New-Object System.Windows.Forms.GroupBox; $gbConfig.Text = "2. Configure Parameters"; $gbConfig.Location = New-Object System.Drawing.Point(15, 85); $gbConfig.Size = New-Object System.Drawing.Size(590, 370)
$lblRemoteUser = New-Object System.Windows.Forms.Label; $lblRemoteUser.Text = "Remote User:"; $lblRemoteUser.Location = New-Object System.Drawing.Point(20, 35); $lblRemoteUser.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtRemoteUser"] = New-Object System.Windows.Forms.TextBox; $controls["txtRemoteUser"].Location = New-Object System.Drawing.Point(180, 32); $controls["txtRemoteUser"].Size = New-Object System.Drawing.Size(390, 20); $controls["txtRemoteUser"].Text = "eXXXXXX"
$lblRemoteHost = New-Object System.Windows.Forms.Label; $lblRemoteHost.Text = "Remote Host:"; $lblRemoteHost.Location = New-Object System.Drawing.Point(20, 65); $lblRemoteHost.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtRemoteHost"] = New-Object System.Windows.Forms.TextBox; $controls["txtRemoteHost"].Location = New-Object System.Drawing.Point(180, 62); $controls["txtRemoteHost"].Size = New-Object System.Drawing.Size(390, 20); $controls["txtRemoteHost"].Text = "hde2stl020003.mastercard.int"
$lblSchema = New-Object System.Windows.Forms.Label; $lblSchema.Text = "Schema:"; $lblSchema.Location = New-Object System.Drawing.Point(20, 95); $lblSchema.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtSchema"] = New-Object System.Windows.Forms.TextBox; $controls["txtSchema"].Location = New-Object System.Drawing.Point(180, 92); $controls["txtSchema"].Size = New-Object System.Drawing.Size(390, 20); $controls["txtSchema"].Text = "your_schema"
$lblTableNameOnly = New-Object System.Windows.Forms.Label; $lblTableNameOnly.Text = "Table Name:"; $lblTableNameOnly.Location = New-Object System.Drawing.Point(20, 125); $lblTableNameOnly.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtTableNameOnly"] = New-Object System.Windows.Forms.TextBox; $controls["txtTableNameOnly"].Location = New-Object System.Drawing.Point(180, 122); $controls["txtTableNameOnly"].Size = New-Object System.Drawing.Size(390, 20); $controls["txtTableNameOnly"].Text = "user_test_table"
$lblToEmail = New-Object System.Windows.Forms.Label; $lblToEmail.Text = "Recipient Email(s):"; $lblToEmail.Location = New-Object System.Drawing.Point(20, 155); $lblToEmail.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtToEmail"] = New-Object System.Windows.Forms.TextBox; $controls["txtToEmail"].Location = New-Object System.Drawing.Point(180, 152); $controls["txtToEmail"].Size = New-Object System.Drawing.Size(390, 20); $controls["txtToEmail"].Text = "name.surname@mastercard.com"
$lblEmailSubject = New-Object System.Windows.Forms.Label; $lblEmailSubject.Text = "Email Subject:"; $lblEmailSubject.Location = New-Object System.Drawing.Point(20, 185); $lblEmailSubject.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtEmailSubject"] = New-Object System.Windows.Forms.TextBox; $controls["txtEmailSubject"].Location = New-Object System.Drawing.Point(180, 182); $controls["txtEmailSubject"].Size = New-Object System.Drawing.Size(390, 20); $controls["txtEmailSubject"].Text = "Data Process Result"
$lblSqlFile = New-Object System.Windows.Forms.Label; $lblSqlFile.Name = "lblSqlFile"; $lblSqlFile.Text = "SQL Query File:"; $lblSqlFile.Location = New-Object System.Drawing.Point(20, 215); $lblSqlFile.Size = New-Object System.Drawing.Size(150, 20)
$controls["txtSqlFile"] = New-Object System.Windows.Forms.TextBox; $controls["txtSqlFile"].Location = New-Object System.Drawing.Point(180, 212); $controls["txtSqlFile"].Size = New-Object System.Drawing.Size(300, 20); $controls["txtSqlFile"].Text = "query.sql"
$btnSqlFile = New-Object System.Windows.Forms.Button; $btnSqlFile.Name = "btnSqlFile"; $btnSqlFile.Text = "Browse..."; $btnSqlFile.Location = New-Object System.Drawing.Point(490, 210); $btnSqlFile.Size = New-Object System.Drawing.Size(80, 25)
$controls["chkAutoGenerateSql"] = New-Object System.Windows.Forms.CheckBox; $controls["chkAutoGenerateSql"].Text = "Auto-generate DROP/CREATE statement (Create Table)"; $controls["chkAutoGenerateSql"].Location = New-Object System.Drawing.Point(180, 245); $controls["chkAutoGenerateSql"].Size = New-Object System.Drawing.Size(390, 20); $controls["chkAutoGenerateSql"].Checked = $true
$controls["chkDownload"] = New-Object System.Windows.Forms.CheckBox; $controls["chkDownload"].Text = "Download result to local folder"; $controls["chkDownload"].Location = New-Object System.Drawing.Point(180, 275); $controls["chkDownload"].Size = New-Object System.Drawing.Size(390, 20); $controls["chkDownload"].Checked = $true

# --- NEW: Monthly Partitioned Job Controls ---
$controls["chkMonthlyJob"] = New-Object System.Windows.Forms.CheckBox; $controls["chkMonthlyJob"].Text = "Process as monthly-partitioned job"; $controls["chkMonthlyJob"].Location = New-Object System.Drawing.Point(20, 305); $controls["chkMonthlyJob"].Size = New-Object System.Drawing.Size(390, 20)
$lblStartDate = New-Object System.Windows.Forms.Label; $lblStartDate.Text = "Start Date:"; $lblStartDate.Location = New-Object System.Drawing.Point(40, 335); $lblStartDate.Size = New-Object System.Drawing.Size(130, 20); $lblStartDate.Visible = $false
$controls["txtStartDate"] = New-Object System.Windows.Forms.TextBox; $controls["txtStartDate"].Location = New-Object System.Drawing.Point(180, 332); $controls["txtStartDate"].Size = New-Object System.Drawing.Size(120, 20); $controls["txtStartDate"].Text = "01/01/2023"; $controls["txtStartDate"].Visible = $false
$lblEndDate = New-Object System.Windows.Forms.Label; $lblEndDate.Text = "End Date:"; $lblEndDate.Location = New-Object System.Drawing.Point(320, 335); $lblEndDate.Size = New-Object System.Drawing.Size(80, 20); $lblEndDate.Visible = $false
$controls["txtEndDate"] = New-Object System.Windows.Forms.TextBox; $controls["txtEndDate"].Location = New-Object System.Drawing.Point(400, 332); $controls["txtEndDate"].Size = New-Object System.Drawing.Size(120, 20); $controls["txtEndDate"].Text = "12/31/2023"; $controls["txtEndDate"].Visible = $false
# --- End of New Controls ---

$gbConfig.Controls.AddRange(@($lblRemoteUser, $controls["txtRemoteUser"], $lblRemoteHost, $controls["txtRemoteHost"], $lblSchema, $controls["txtSchema"], $lblTableNameOnly, $controls["txtTableNameOnly"], $lblToEmail, $controls["txtToEmail"], $lblEmailSubject, $controls["txtEmailSubject"], $lblSqlFile, $controls["txtSqlFile"], $btnSqlFile, $controls["chkAutoGenerateSql"], $controls["chkDownload"], $controls["chkMonthlyJob"], $lblStartDate, $controls["txtStartDate"], $lblEndDate, $controls["txtEndDate"]))

$gbAction = New-Object System.Windows.Forms.GroupBox; $gbAction.Text = "3. Execute and Monitor"; $gbAction.Location = New-Object System.Drawing.Point(15, 465); $gbAction.Size = New-Object System.Drawing.Size(590, 310)
$controls["runButton"] = New-Object System.Windows.Forms.Button; $controls["runButton"].Text = "1. Launch & Prepare Download"; $controls["runButton"].Location = New-Object System.Drawing.Point(20, 30); $controls["runButton"].Size = New-Object System.Drawing.Size(220, 35); $controls["runButton"].Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$controls["downloadButton"] = New-Object System.Windows.Forms.Button; $controls["downloadButton"].Text = "2. Download Result"; $controls["downloadButton"].Location = New-Object System.Drawing.Point(250, 30); $controls["downloadButton"].Size = New-Object System.Drawing.Size(150, 35); $controls["downloadButton"].Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold); $controls["downloadButton"].Enabled = $false
$controls["resetButton"] = New-Object System.Windows.Forms.Button; $controls["resetButton"].Text = "Reset"; $controls["resetButton"].Location = New-Object System.Drawing.Point(410, 30); $controls["resetButton"].Size = New-Object System.Drawing.Size(75, 35); $controls["resetButton"].Enabled = $false
$controls["logButton"] = New-Object System.Windows.Forms.Button; $controls["logButton"].Text = "Open Log"; $controls["logButton"].Location = New-Object System.Drawing.Point(495, 30); $controls["logButton"].Size = New-Object System.Drawing.Size(75, 35); $controls["logButton"].Enabled = $false
$lblStatus = New-Object System.Windows.Forms.Label; $lblStatus.Text = "Status Log:"; $lblStatus.Location = New-Object System.Drawing.Point(20, 75); $lblStatus.Size = New-Object System.Drawing.Size(100, 20)
$statusBox = New-Object System.Windows.Forms.TextBox; $statusBox.Name = "statusBox"; $statusBox.Location = New-Object System.Drawing.Point(20, 95); $statusBox.Size = New-Object System.Drawing.Size(550, 200); $statusBox.ReadOnly = $true; $statusBox.Multiline = $true; $statusBox.Scrollbars = "Vertical"; $statusBox.Font = New-Object System.Drawing.Font("Consolas", 8); $statusBox.BackColor = [System.Drawing.Color]::White
$gbAction.Controls.AddRange(@($controls["runButton"], $controls["downloadButton"], $controls["resetButton"], $controls["logButton"], $lblStatus, $statusBox))
$script:form.Controls.AddRange(@($gbMode, $gbConfig, $gbAction))

# --- 2. DEFINE ACTIONS (EVENT HANDLERS) ---
function Set-UiState { param([string]$State)
    switch ($State) {
        "Initial" { $gbConfig.Controls | ForEach-Object { $_.Enabled = $true }; $gbMode.Controls | ForEach-Object { $_.Enabled = $true }; $controls.runButton.Enabled = $true; $controls.downloadButton.Enabled = $false; $controls.resetButton.Enabled = $false }
        "Processing" { $gbConfig.Controls | ForEach-Object { $_.Enabled = $false }; $gbMode.Controls | ForEach-Object { $_.Enabled = $false }; $controls.runButton.Enabled = $false; $controls.downloadButton.Enabled = $false; $controls.resetButton.Enabled = $true }
        "ReadyForDownload" { $gbConfig.Controls | ForEach-Object { $_.Enabled = $false }; $gbMode.Controls | ForEach-Object { $_.Enabled = $false }; $controls.runButton.Enabled = $false; $controls.downloadButton.Enabled = $true; $controls.resetButton.Enabled = $true }
    }
}
function Test-Inputs {
    $errors = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace($controls.txtRemoteUser.Text)) { $errors.Add("• Remote User cannot be empty.") }
    if ([string]::IsNullOrWhiteSpace($controls.txtRemoteHost.Text)) { $errors.Add("• Remote Host cannot be empty.") }

    if ($controls.radioDownload.Checked) { # Download Existing Table Mode
        if ([string]::IsNullOrWhiteSpace($controls.txtSchema.Text)) { $errors.Add("• Schema cannot be empty.") }
        if ([string]::IsNullOrWhiteSpace($controls.txtTableNameOnly.Text)) { $errors.Add("• Table Name cannot be empty.") }
    } else { # Create or Query Mode
        $sqlFile = $controls.txtSqlFile.Text
        if ([string]::IsNullOrWhiteSpace($sqlFile)) { $errors.Add("• SQL Query File cannot be empty.") } 
        elseif (-not (Test-Path -Path $sqlFile -PathType Leaf)) { $errors.Add("• SQL Query File not found: `"$sqlFile`"") }

        if ($controls.chkAutoGenerateSql.Checked) { # Create Table sub-mode
            if ([string]::IsNullOrWhiteSpace($controls.txtSchema.Text)) { $errors.Add("• Schema cannot be empty.") }
            if ([string]::IsNullOrWhiteSpace($controls.txtTableNameOnly.Text)) { $errors.Add("• Table Name cannot be empty.") }
            if ([string]::IsNullOrWhiteSpace($controls.txtToEmail.Text)) { $errors.Add("• Recipient Email(s) cannot be empty.") }
            if ([string]::IsNullOrWhiteSpace($controls.txtEmailSubject.Text)) { $errors.Add("• Email Subject cannot be empty.") }
        }
    }
    if ($errors.Count -gt 0) {
        $errorMessage = "Please correct the following errors:`n`n" + ($errors -join "`n");
        [System.Windows.Forms.MessageBox]::Show($errorMessage, "Validation Error", "OK", "Error") | Out-Null; return $false
    }
    return $true
}
$AutoGenerateSqlCheckAction = {
    # This action is now only responsible for what happens when the "Auto-generate" checkbox is toggled.
    $isAutoGenerate = $controls.chkAutoGenerateSql.Checked
    # When not auto-generating, the user is in the "Query & Download" flow which does not need these fields.
    $controls.txtSchema.Enabled = $isAutoGenerate
    $controls.txtTableNameOnly.Enabled = $isAutoGenerate
}
$DownloadCheckAction = {
    if ($controls.radioCreate.Checked) {
        $controls.downloadButton.Visible = $controls.chkDownload.Checked
        $controls.runButton.Text = if ($controls.chkDownload.Checked) { "1. Launch & Prepare Download" } else { "1. Launch & Process" }
    }
}
$ModeChangeAction = {
    $isCreateMode = $controls.radioCreate.Checked
    $controls.txtToEmail.Enabled = $isCreateMode; $controls.txtEmailSubject.Enabled = $isCreateMode; $controls.txtSqlFile.Enabled = $isCreateMode; $btnSqlFile.Enabled = $isCreateMode; $controls.chkAutoGenerateSql.Enabled = $isCreateMode; $controls.chkDownload.Enabled = $isCreateMode
    $controls.txtSchema.Enabled = -not $isCreateMode; $controls.txtTableNameOnly.Enabled = -not $isCreateMode
    if ($isCreateMode) {
        $AutoGenerateSqlCheckAction.Invoke(); $DownloadCheckAction.Invoke()
    } else {
        $controls.downloadButton.Visible = $true; $controls.runButton.Text = "1. Prepare for Download"; $controls.txtSchema.Enabled = $true; $controls.txtTableNameOnly.Enabled = $true
    }
}
$controls.radioCreate.Add_CheckedChanged($ModeChangeAction); $controls.radioDownload.Add_CheckedChanged($ModeChangeAction)
$controls.chkDownload.Add_CheckedChanged($DownloadCheckAction); $controls.chkAutoGenerateSql.Add_CheckedChanged($AutoGenerateSqlCheckAction)
$btnSqlFile.Add_Click({ $dialog = New-Object System.Windows.Forms.OpenFileDialog; $dialog.Filter = "SQL Scripts (*.sql)|*.sql"; if ($dialog.ShowDialog() -eq 'OK') { $controls.txtSqlFile.Text = $dialog.FileName } })
$controls.logButton.Add_Click({ if ($script:currentLogFile -and (Test-Path $script:currentLogFile)) { Invoke-Item $script:currentLogFile } })
$controls.resetButton.Add_Click({ Write-Log "UI has been reset."; $statusBox.Text = ""; $script:sharedConfig = $null; $script:remoteCsvFullPath = ""; Set-UiState -State "Initial"; $ModeChangeAction.Invoke() })

# --- UPDATED: Event handler for the monthly job checkbox ---
$MonthlyJobCheckAction = {
    $isMonthlyJob = $controls.chkMonthlyJob.Checked
    # Show/hide date fields
    $lblStartDate.Visible = $isMonthlyJob
    $controls.txtStartDate.Visible = $isMonthlyJob
    $lblEndDate.Visible = $isMonthlyJob
    $controls.txtEndDate.Visible = $isMonthlyJob
    
    # When monthly job is active, auto-generate and download workflows are not applicable
    $controls.chkAutoGenerateSql.Enabled = -not $isMonthlyJob
    $controls.chkDownload.Enabled = -not $isMonthlyJob
    
    if ($isMonthlyJob) {
        # Ensure core fields required by the monthly job workflow are enabled.
        $controls.txtSchema.Enabled = $true
        $controls.txtTableNameOnly.Enabled = $true
        $controls.txtToEmail.Enabled = $true
        $controls.txtEmailSubject.Enabled = $true
        
        # Uncheck the other workflow boxes to avoid UI confusion.
        $controls.chkAutoGenerateSql.Checked = $false
        $controls.chkDownload.Checked = $false
    } else {
        # When unchecked, revert to the state defined by the "Auto-generate" checkbox
        $AutoGenerateSqlCheckAction.Invoke()
    }
}
$controls.chkMonthlyJob.Add_CheckedChanged($MonthlyJobCheckAction)

# --- Main Logic Step 1: Prepare and Upload ---
$controls.runButton.Add_Click({
    if (-not (Test-Inputs)) { return }
    Set-UiState -State "Processing"; $statusBox.Text = ""
    $runTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"; $script:currentLogFile = Join-Path -Path $PSScriptRoot -ChildPath "launcher_log_$runTimestamp.log"; $controls.logButton.Enabled = $true
    Write-Log "Log session started."
    
    $script:sharedConfig = @{ RemoteUser = $controls.txtRemoteUser.Text; Schema = $controls.txtSchema.Text; TableNameOnly = $controls.txtTableNameOnly.Text; ToEmail = $controls.txtToEmail.Text; EmailSubject = $controls.txtEmailSubject.Text; SqlFilePath = $controls.txtSqlFile.Text; RemoteHost = $controls.txtRemoteHost.Text; SshPort = 2222; RunTimestamp = $runTimestamp }
    $script:sharedConfig["FullTableName"] = "$($script:sharedConfig.Schema).$($script:sharedConfig.TableNameOnly)"
    Write-Log "--- Run Parameters ---"; $script:sharedConfig.GetEnumerator() | ForEach-Object { Write-Log "- $($_.Name): $($_.Value)" }; Write-Log "----------------------"

    $remoteUserDir = "/ads_storage/$($script:sharedConfig.RemoteUser)"; $remoteLauncherDir = "/ads_storage/hadoop_query_launcher/scr"
    $remoteHostLogin = "$($script:sharedConfig.RemoteUser)@$($script:sharedConfig.RemoteHost)"
    $localTempSqlFilePath = $null
    
    try {
        if ($controls.chkMonthlyJob.Checked) {
            # WORKFLOW: Monthly Partitioned Job
            $script:sharedConfig["Mode"] = "MonthlyJob"
            Write-Log "Starting 'Monthly Partitioned Job' workflow..."

            # Additional validation for dates
            if ([string]::IsNullOrWhiteSpace($controls.txtStartDate.Text) -or [string]::IsNullOrWhiteSpace($controls.txtEndDate.Text)) {
                throw "Start Date and End Date cannot be empty for a monthly job."
            }

            $sqlFileToUpload = $controls.txtSqlFile.Text
            $remoteSqlFileName = Split-Path -Path $sqlFileToUpload -Leaf
            Write-Log "Step 1: Uploading SQL template file..."
            Invoke-Expression "scp -P $($script:sharedConfig.SshPort) -C `"$sqlFileToUpload`" `"$remoteHostLogin`:$remoteUserDir/`"" 2>&1 | Out-Null
            if ($LASTEXITCODE -ne 0) { throw "Failed to upload SQL file." }

            $pythonExecutable = "/sys_apps_01/python/python310/bin/python3.10"
            $remotePythonScript = "$remoteLauncherDir/monthly_query_processor.py" # New script
            $arguments = ('--sql-file "{0}" --schema "{1}" --table-name "{2}" --start-date "{3}" --end-date "{4}" --user "{5}" --to-email "{6}" --subject "{7}"' -f `
                $remoteSqlFileName, $script:sharedConfig.Schema, $script:sharedConfig.TableNameOnly, $controls.txtStartDate.Text, $controls.txtEndDate.Text, $script:sharedConfig.RemoteUser, $script:sharedConfig.ToEmail, $script:sharedConfig.EmailSubject)

            $sessionFolderName = "session_monthly_$($script:sharedConfig.TableNameOnly)_$runTimestamp"
            $remoteSessionFolderPath = "$remoteUserDir/$sessionFolderName"
            $createDirCmd = "mkdir -p $remoteSessionFolderPath"
            $nohupLogFile = "$remoteSessionFolderPath/monthly_job.log"; $pidFile = "$remoteSessionFolderPath/run.pid"
            $runAndMonitorCmd = "nohup $pythonExecutable $remotePythonScript $arguments > $nohupLogFile 2>&1 & echo `$! > $pidFile; tail -f $nohupLogFile --pid=`$(cat $pidFile)"
            $script:sharedConfig["RemoteExecuteCommand"] = "cd $remoteUserDir; $createDirCmd; $runAndMonitorCmd"

        } elseif ($controls.radioDownload.Checked) {
            # WORKFLOW: Download Existing Table
            $script:sharedConfig["Mode"] = "Download"
            Write-Log "Starting 'Download Only' workflow..."

            $remoteCsvFile = "$($script:sharedConfig.TableNameOnly)_$runTimestamp.csv"
            $script:remoteCsvFullPath = "$remoteUserDir/$($remoteCsvFile).gz"
            
            $pythonExecutable = "/sys_apps_01/python/python310/bin/python3.10"
            $remotePythonScript = "$remoteLauncherDir/download_to_csv.py"
            $arguments = "--table-name `"$($script:sharedConfig.FullTableName)`" --output-file `"$remoteUserDir/$remoteCsvFile`""
            
            $nohupLogFile = "$remoteUserDir/download_job_$runTimestamp.log"
            $pidFile = "$remoteUserDir/download_job_$runTimestamp.pid"
            $runAndMonitorCmd = "nohup $pythonExecutable $remotePythonScript $arguments > $nohupLogFile 2>&1 && gzip `"$remoteUserDir/$remoteCsvFile`" & echo `$! > $pidFile; tail -f $nohupLogFile --pid=`$(cat $pidFile)"
            $script:sharedConfig["RemoteExecuteCommand"] = "cd $remoteUserDir; $runAndMonitorCmd"
        
        } else { # "Create or Query from SQL file" is checked
            if ($controls.chkAutoGenerateSql.Checked) {
                # WORKFLOW: Create Table (with or without download)
                $script:sharedConfig["Mode"] = "Create"
                Write-Log "Starting 'Create and Process' workflow..."

                $sqlFileToUpload = $script:sharedConfig.SqlFilePath
                $hdfsTableName = $script:sharedConfig.FullTableName -replace '[.:]', '_'; $schemaPrefix = ($script:sharedConfig.Schema -split '_')[0]; $hdfsLocation = "/das/$schemaPrefix/enc/$($script:sharedConfig.RemoteUser)/$hdfsTableName"
                $sqlHeader = "DROP TABLE IF EXISTS $($script:sharedConfig.FullTableName);`r`n`r`nCREATE TABLE $($script:sharedConfig.FullTableName)`r`nSTORED AS PARQUET`r`nLOCATION '$hdfsLocation' AS`r`n`r`n"
                $originalSqlContent = Get-Content -Path $script:sharedConfig.SqlFilePath -Raw
                $localTempSqlFilePath = Join-Path -Path $PSScriptRoot -ChildPath "_temp_query_$runTimestamp.sql"
                $remoteSqlFileName = Split-Path -Path $localTempSqlFilePath -Leaf
                Set-Content -Path $localTempSqlFilePath -Value ($sqlHeader + $originalSqlContent)
                
                Write-Log "Step 1: Uploading SQL file..."
                Invoke-Expression "scp -P $($script:sharedConfig.SshPort) -C `"$localTempSqlFilePath`" `"$remoteHostLogin`:$remoteUserDir/`"" 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "Failed to upload SQL file." }
                
                $sessionFolderName = "session_$($script:sharedConfig.TableNameOnly)_$runTimestamp"
                $remoteSessionFolderPath = "$remoteUserDir/$sessionFolderName"
                $script:sharedConfig["RemoteSessionFolder"] = $remoteSessionFolderPath

                $pythonExecutable = "/sys_apps_01/python/python310/bin/python3.10"
                $remotePythonScript = "$remoteLauncherDir/Query_Impala_Parametrized.py"
                $arguments = '--sql-file "{0}" --table-name "{1}" --to-email "{2}" --subject "{3}" --user "{4}" --session-folder "{5}"' -f $remoteSqlFileName, $script:sharedConfig.FullTableName, $script:sharedConfig.ToEmail, $script:sharedConfig.EmailSubject, $script:sharedConfig.RemoteUser, $remoteSessionFolderPath
                if ($controls.chkDownload.Checked) { $arguments += " --download" }
                
                $createDirCmd = "mkdir -p $remoteSessionFolderPath"
                $nohupLogFile = "$remoteSessionFolderPath/create_process.log"; $pidFile = "$remoteSessionFolderPath/run.pid"
                $runAndMonitorCmd = "nohup $pythonExecutable $remotePythonScript $arguments > $nohupLogFile 2>&1 & echo `$! > $pidFile; tail -f $nohupLogFile --pid=`$(cat $pidFile)"
                $script:sharedConfig["RemoteExecuteCommand"] = "cd $remoteUserDir; $createDirCmd; $runAndMonitorCmd"
            
            } elseif ($controls.chkDownload.Checked) {
                # WORKFLOW: Query & Download (Auto-generate is OFF, Download is ON)
                $script:sharedConfig["Mode"] = "QueryAndDownload"
                Write-Log "Starting 'Query and Download' workflow..."

                $sqlFileToUpload = $controls.txtSqlFile.Text
                $remoteSqlFileName = Split-Path -Path $sqlFileToUpload -Leaf
                Write-Log "Step 1: Uploading SQL file..."
                Invoke-Expression "scp -P $($script:sharedConfig.SshPort) -C `"$sqlFileToUpload`" `"$remoteHostLogin`:$remoteUserDir/`"" 2>&1 | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "Failed to upload SQL file." }

                $remoteCsvFile = "query_result_$runTimestamp.csv"
                $script:remoteCsvFullPath = "$remoteUserDir/$($remoteCsvFile).gz"
                
                $pythonExecutable = "/sys_apps_01/python/python310/bin/python3.10"
                $remotePythonScript = "$remoteLauncherDir/download_to_csv.py"
                $arguments = "--query-file `"$remoteSqlFileName`" --output-file `"$remoteUserDir/$remoteCsvFile`""

                $nohupLogFile = "$remoteUserDir/query_job_$runTimestamp.log"; $pidFile = "$remoteUserDir/query_job_$runTimestamp.pid"
                $runAndMonitorCmd = "nohup $pythonExecutable $remotePythonScript $arguments > $nohupLogFile 2>&1 && gzip `"$remoteUserDir/$remoteCsvFile`" & echo `$! > $pidFile; tail -f $nohupLogFile --pid=`$(cat $pidFile)"
                $script:sharedConfig["RemoteExecuteCommand"] = "cd $remoteUserDir; $runAndMonitorCmd"
            
            } else {
                # UNSUPPORTED: Auto-generate is OFF, Download is OFF
                [System.Windows.Forms.MessageBox]::Show("This combination of options is not supported.`n`nPlease either check 'Auto-generate' to create a table, or check 'Download result' to run the query and download its output.", "Unsupported Operation", "OK", "Warning") | Out-Null
                Set-UiState -State "Initial"; $ModeChangeAction.Invoke(); return
            }
        }
        # --- Common Steps: Launch Terminal, Instruct ---
        Set-Clipboard -Value $script:sharedConfig.RemoteExecuteCommand
        Write-Log "Step 2: Launching SSH terminal..."; $sshArgs = "-p $($script:sharedConfig.SshPort) -t $remoteHostLogin"
        if (Get-Command wt.exe -ErrorAction SilentlyContinue) { Start-ProcessAndMoveWindow -ProcessName "WindowsTerminal" -FilePath "wt.exe" -ArgumentList "ssh $sshArgs" -X 10 -Y 10 } 
        else { Start-ProcessAndMoveWindow -ProcessName "powershell" -FilePath "powershell.exe" -ArgumentList "ssh $sshArgs" -X 10 -Y 10 }

        $instructions = "--- ACTION REQUIRED ---`n1. The SSH terminal has been opened.`n2. Once connected and authenticated (kinit), paste the command from your clipboard to start the process.`n3. The terminal will close AUTOMATICALLY when the job is complete.`n4. Return here and click '2. Download Result' (if applicable)."
        Write-Log "Step 3: Ready for remote execution." $instructions
        if ($controls.downloadButton.Visible) { Set-UiState -State "ReadyForDownload" }
    } catch {
        Write-Log "An error occurred: $($_.Exception.Message)" -IsError; Set-UiState -State "Initial"; $ModeChangeAction.Invoke()
    } finally {
        if ($localTempSqlFilePath -and (Test-Path $localTempSqlFilePath)) { Write-Log "Cleaning up local temp file..."; Remove-Item -Path $localTempSqlFilePath -Force }
    }
})

# --- Main Logic Step 2: Download Result ---
$controls.downloadButton.Add_Click({
    $controls.downloadButton.Enabled = $false
    if (-not $script:sharedConfig) { Write-Log "Configuration is missing. Please start from step 1." -IsError; return }
    $remoteHostLogin = "$($script:sharedConfig.RemoteUser)@$($script:sharedConfig.RemoteHost)"
    $downloadCommand = ""; $targetPath = ""

    if ($script:sharedConfig.Mode -eq "Create") {
        $remoteSessionFolder = $script:sharedConfig.RemoteSessionFolder
        if (-not $remoteSessionFolder) { Write-Log "Could not determine the remote session folder." -IsError; return }
        Write-Log "Downloading session folder: $remoteSessionFolder"
        $downloadCommand = "scp -P $($script:sharedConfig.SshPort) -r $remoteHostLogin`:`"$($remoteSessionFolder)`" `"$PSScriptRoot`""
        $targetPath = Join-Path -Path $PSScriptRoot -ChildPath "session_$($script:sharedConfig.RunTimestamp)"
    } elseif ($script:sharedConfig.Mode -eq "Download" -or $script:sharedConfig.Mode -eq "QueryAndDownload") {
        if (-not $script:remoteCsvFullPath) { Write-Log "Could not determine the remote file path." -IsError; return }
        Write-Log "Downloading result file: $($script:remoteCsvFullPath)"
        $downloadCommand = "scp -P $($script:sharedConfig.SshPort) $remoteHostLogin`:`"$($script:remoteCsvFullPath)`" `"$PSScriptRoot`""
        $targetPath = Join-Path -Path $PSScriptRoot -ChildPath (Split-Path $script:remoteCsvFullPath -Leaf)
    } else { Write-Log "Unknown mode in configuration. Cannot download." -IsError; return }

    Write-Log "Executing Download..." $downloadCommand
    $scpResult = Invoke-Expression $downloadCommand 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Log "Download failed. Check if file/folder exists on the server." -IsError -Detail $scpResult } 
    else { Write-Log "Download completed successfully to '$targetPath'." }
})

# --- 3. SHOW THE FORM ---
$script:form.Add_Shown({
    # Correctly and robustly calculate the form's starting position
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    if ($null -eq $screen) {
        # Fallback to the first available screen if no primary is designated
        $screen = [System.Windows.Forms.Screen]::AllScreens[0]
    }
    
    $x_pos = $screen.WorkingArea.Width - $script:form.Width - 10
    $y_pos = 10
    $script:form.Location = New-Object System.Drawing.Point($x_pos, $y_pos)
    
    # Set initial UI state
    Set-UiState -State "Initial"
    $ModeChangeAction.Invoke()
    $MonthlyJobCheckAction.Invoke()
})

[void]$script:form.ShowDialog()
$script:form.Dispose()