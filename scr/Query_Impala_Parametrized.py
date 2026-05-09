import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import logging
import subprocess
import argparse
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================================================================
# Main Functions
# =============================================================================

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description='Execute a SQL query from a file, create a table, and send an email notification.')
    parser.add_argument('--sql-file', dest='sql_file', required=True,
                        help='Path to the .sql file containing the query to execute.')
    parser.add_argument('--table-name', dest='table_name', required=True,
                        help='Name of the table to be created (e.g., schema.tablename).')
    parser.add_argument('--to-email', dest='to_email', required=True,
                        help='Recipient email address(es). For multiple emails, separate with a semicolon (;).')
    parser.add_argument('--subject', dest='subject', required=True,
                        help='Subject line for the notification email.')
    parser.add_argument('--user', required=True, help='The remote user ID running the script.')
    parser.add_argument('--download', action='store_true', help='If set, export the created table to a CSV file.')
    parser.add_argument('--session-folder', dest='session_folder', required=True,
                        help='Full path to a unique session folder for all outputs.')

    args = parser.parse_args()

    # Assign variables from arguments
    tablecreated = args.table_name
    to_email = args.to_email
    subject = args.subject
    sql_query = load_query(args.sql_file)

    # Static variables that are not passed as arguments
    filas = ["adhoc_fast", "acs_small", "adhoc_small", "acs_large","adhoc"]

    print("--- Script Configuration ---")
    print(f"User: {args.user}")
    print(f"Table to be created: {tablecreated}")
    print(f"Recipient Emails: {to_email}")
    print(f"Email Subject: {subject}")
    print(f"Download Requested: {'Yes' if args.download else 'No'}")
    print("--------------------------")

    ## The sql_query variable is now populated from the file content
    print("\nExecuting the following SQL query:")
    print("="*40)
    print(sql_query)
    print("="*40)

    try:
        os.makedirs(args.session_folder, exist_ok=True)
        print(f"Ensured session directory exists: {args.session_folder}")
    except OSError as e:
        print(f"Error creating session directory: {e}")
        sys.exit(1)

    SUCCESS = retry_loop(sql_query, filas, to_email, subject, tablecreated, args.user)
    if SUCCESS and args.download:
        time.sleep(10)
        export_table_to_csv(tablecreated, args.user, args.session_folder, to_email, subject)

def retry_loop(sql_query, filas, to_email, subject, tablecreated, user):
    messageBody = (
        f"User: {user}\n"
        f"Process: Table Creation\n"
        f"Table: {tablecreated}\n\n"
        "The script has started and will now attempt to execute the query."
    )
    subject_start = f"{subject} - PROCESSO INICIADO"
    send_email(messageBody, subject_start, to_email)

    sucesso = False
    retry_cnt = 1
    while not sucesso:
        for fila in filas:
            try:
                sql_pool = f"set request_pool={fila};"
                sql = sql_pool + " " + sql_query
                sucesso = run_on_impala(sql, subject, to_email, tablecreated, user, fila)
                if sucesso:
                    break  # Exit for and while loops
            except Exception as e:
                print(f"Erro na fila {fila}: {e}")
                time.sleep(2)
                continue  # Try the next queue
        if not sucesso:
            print("Nenhuma fila funcionou. Aguardando 30 segundos antes de tentar novamente...\n")
            messageBody = (
                f"User: {user}\n"
                f"Table: {tablecreated}\n"
                f"Attempt: {retry_cnt}\n\n"
                "All Impala queues (adhoc_fast, adhoc_small, adhoc) are currently busy. \n"
                "The script will wait for 30 seconds and then retry the execution cycle. "
                "You will be notified upon success or fatal error."
            )
            subject_filaCheia = f"{subject} - (Attempt {retry_cnt}) All Queues Full"
            send_email(messageBody, subject_filaCheia, to_email)
            retry_cnt += 1
            time.sleep(30)

    return sucesso

# =============================================================================
# Helper Functions
# =============================================================================

def export_table_to_csv(table_name, user, session_folder, to_email, subject):
    """
    Exports an Impala table to a CSV file and notifies via email.
    """
    print("\n--- Starting CSV Export and Compression Process ---")
    
    start_message = (
        f"User: {user}\n"
        f"Process: CSV Export\n"
        f"Table: {table_name}\n\n"
        f"The table creation was successful. Now starting the CSV export process. "
        f"The output will be placed in the session folder:\n{session_folder}"
    )
    send_email(start_message, f"{subject} - CSV EXPORT STARTED", to_email)

    try:
        table_name_only = table_name.split('.')[-1]
        output_csv_file = os.path.join(session_folder, f"{table_name_only}.csv")
        final_gzipped_file = f"{output_csv_file}.gz"

        # Step 1: Execute download_to_csv.py
        print(f"Calling download_to_csv.py to export {table_name} to {output_csv_file}...")
        # MODIFIED: Added the central launcher directory to the python command
        command_export = ['python', '/ads_storage/hadoop_query_launcher/scr/download_to_csv.py', '--table-name', table_name, '--output-file', output_csv_file]
        subprocess.run(command_export, check=True)
        print(f"Successfully exported data to {output_csv_file}")

        # Step 2: Compress the exported CSV file
        print(f"Compressing {output_csv_file} to {final_gzipped_file}...")
        command_compress = ['gzip', output_csv_file]
        subprocess.run(command_compress, check=True)
        print(f"Successfully compressed file. Final output is {final_gzipped_file}")
        
        success_message = (
            f"User: {user}\n"
            f"Process: CSV Export\n"
            f"Status: SUCCESS\n\n"
            f"The table '{table_name}' has been successfully exported and compressed.\n"
            f"The final file is located at:\n{final_gzipped_file}"
        )
        send_email(success_message, f"{subject} - CSV EXPORT FINISHED", to_email)
        print(f"\n[SUCCESS] Export and compression process completed.")

    except (FileNotFoundError, subprocess.CalledProcessError, Exception) as e:
        # MODIFIED: Improved error message to be more detailed
        error_message = (
            f"User: {user}\n"
            f"Process: CSV Export\n"
            f"Status: FAILED\n\n"
            f"An error occurred during the CSV export or compression for table '{table_name}'.\n"
            f"Please check the script logs for more details.\n\n"
            f"Error Details:\n{e}"
        )
        send_email(error_message, f"{subject} - CSV EXPORT FAILED", to_email)
        print(f"\n[ERROR] An error occurred during the CSV export process: {e}")
        raise

def load_query(path):
    try:
        with open(path, 'r') as f:
            sql_query = f.read()
        print(f"Successfully loaded SQL from '{path}'")
    except FileNotFoundError:
        print(f"Error: The file '{path}' was not found.")
        sys.exit(1)
    return sql_query

def send_email(messageBody, subject, to_email):
    msg = MIMEMultipart()
    from_email = 'AutoQueryExecution_Analytics@mastercard.com'
    msg['From'] = from_email
    msg['TO'] = to_email
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(messageBody))
    
    try:
        server = smtplib.SMTP("mailhost.mclocal.int")
        server.sendmail(from_email, to_email.split(';'), msg.as_string())
        server.quit()
        logging.info(f"Email sent to {to_email} with subject: {subject}")
    except Exception as e:
        logging.error(f"Failed to send email. Error: {e}")

# MODIFIED: The function now returns the full error text along with the category
def classificar_erro_impala(stderr_text: str) -> dict:
    texto = stderr_text.lower()
    details = {"detalhes": stderr_text} # ADDED: Dictionary to hold details
    if "memory limit exceeded" in texto:
        return {"categoria": "MEMORY_EXCEEDED", **details}
    elif 'not enough memory available' in texto:
        return {"categoria": "MEMORY_EXCEEDED", **details}
    elif "syntax error" in texto or "parseexception" in texto:
        return {"categoria": "SYNTAX_ERROR", **details}
    elif "authenticationexception" in texto:
        return {"categoria": "AUTH_ERROR", **details}
    elif "table not found" in texto or "could not resolve" in texto:
        return {"categoria": "TABLE_NOT_FOUND", **details}
    elif "timed out" in texto or "deadline exceeded" in texto:
        return {"categoria": "TIMEOUT", **details}
    elif "queue is full" in texto or "no resources available" in texto:
        return {"categoria": "QUEUE_FULL", **details}
    elif "could not connect" in texto or "connection refused" in texto:
        return {"categoria": "CONNECTION_ERROR", **details}
    elif "dropped due to backpressure" in texto:
        return {"categoria": "BACKPRESSURE", **details}
    elif "could not resolve host" in texto or "name or service not known" in texto:
        return {"categoria": "HOST_RESOLUTION_ERROR", **details}
    elif "invalid credentials" in texto or "authentication failed" in texto:
        return {"categoria": "AUTH_ERROR", **details}
    elif "invalid or unknown query handle" in texto:
        return {"categoria": "TIMEOUT", **details}
    elif "time limit" in texto:
        return {"categoria": "TIMEOUT", **details}
    elif "duplicate column name" in texto:
        return {"categoria": "DUPLICATE_COLUMN", **details}
    elif "connection reset" in texto or "connection refused" in texto:
        return {"categoria": "CONNECTION_ERROR", **details}
    elif "unreachable" in texto:
        return {"categoria": "HOST_UNREACHABLE", **details}
    elif "diskspace" in texto or "disk full" in texto:
        return {"categoria": "DISK_FULL", **details}
    elif "memory available" in texto:
        return {"categoria": "MEMORY_AVAILABLE", **details}
    elif "space limit" in texto:
        return {"categoria": "SPACE_LIMIT", **details}
    elif "timeout" in texto:
        return {"categoria": "TIMEOUT", **details}
    else:
        return {"categoria": "GENERIC_ERROR", **details}

def run_on_impala(query: str, subject, to_email, tablecreated="", user="", queue=""):
    process = subprocess.Popen(
        ['impala-shell', '-k', '-i', 'dw.prod.impala.mastercard.int:21000', '--ssl', '--delimited', '--print_header',
         '--output_delimiter=|', '-q', query], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    logging.info("Executing query: %s" % query)

    if process.returncode == 0:
        print("########## query executed successfully ##########")
        messageBody = (
            f"User: {user}\n"
            f"Process: Table Creation\n"
            f"Status: SUCCESS\n"
            f"Table Created: {tablecreated}\n"
            f"Succeeded on Queue: {queue}\n\n"
            "The SQL query was executed successfully."
        )
        subject_success = f"{subject} - PROCESSO FINALIZADO"
        send_email(messageBody, subject_success, to_email)
        logging.debug(stdout.decode())
        return True
    else:
        print("********ERROR********")
        stderr_decoded = stderr.decode()
        erro_classificado = classificar_erro_impala(stderr_decoded)
        print(f"Erro mapeado: {erro_classificado['categoria']}")
        
        error_list = [
                "TABLE_NOT_FOUND",
                "SYNTAX_ERROR",
                "DUPLICATE_COLUMN",
                "GENERIC_ERROR",
                ]
        if erro_classificado['categoria'] in error_list:
            messageBody = (
                f"User: {user}\n"
                f"Process: Table Creation\n"
                f"Status: FATAL ERROR\n"
                f"Table: {tablecreated}\n"
                f"Failed on Queue: {queue}\n"
                f"Error Type: {erro_classificado['categoria']}\n\n"
                f"A fatal error occurred, and the process will not be retried. Please review the details below.\n\n"
                f"------------------- ERROR TRACE -------------------\n"
                f"{erro_classificado['detalhes']}\n"
                f"---------------------------------------------------\n"
            )
            subject_error = f"{subject} - ERRO ({erro_classificado['categoria']})"
            send_email(messageBody, subject_error, to_email)
            logging.debug(stdout.decode())
            return True # Return True to stop retries for fatal errors
        else:
            ## Retriable Error Message
            messageBody = (
                f"User: {user}\n"
                f"Process: Table Creation\n"
                f"Status: RETRIABLE ERROR\n"
                f"Table: {tablecreated}\n"
                f"Queue Attempted: {queue}\n"
                f"Error Type: {erro_classificado['categoria']}\n\n"
                f"A retriable error occurred. The script will attempt to run the query again using the next available queue.\n\n"
                f"------------------- ERROR TRACE -------------------\n"
                f"{erro_classificado['detalhes']}\n"
                f"---------------------------------------------------\n"
            )
            subject_retry = f"{subject} - RETRIABLE ERROR ({erro_classificado['categoria']})"
            send_email(messageBody, subject_retry, to_email)
        return False

if __name__ == '__main__':
    main()