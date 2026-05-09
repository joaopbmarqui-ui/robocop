import os
import subprocess
import time
import logging
import argparse
import sys

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================================================================
# Helper Functions
# =============================================================================

def classificar_erro_impala(stderr_text: str) -> dict:
    """
    Classifies an Impala error based on the content of its stderr.
    """
    texto = stderr_text.lower()
    details = {"detalhes": stderr_text}

    if "memory limit exceeded" in texto:
        return {"categoria": "MEMORY_EXCEEDED", **details}
    elif "syntax error" in texto or "parseexception" in texto:
        return {"categoria": "SYNTAX_ERROR", **details}
    elif "authenticationexception" in texto:
        return {"categoria": "AUTH_ERROR", **details}
    elif "table not found" in texto or "could not resolve" in texto:
        return {"categoria": "TABLE_NOT_FOUND", **details}
    elif "timed out" in texto or "deadline exceeded" in texto:
        return {"categoria": "TIMEOUT", **details}
    else:
        return {"categoria": "GENERIC_ERROR", **details}


def run_export_on_impala(query: str, output_file: str):
    """
    Executes an Impala query to export data to a CSV file.
    """
    command = [
        'impala-shell', '-k', '-i', 'dw.prod.impala.mastercard.int:21000', '--ssl',
        '--delimited', '--print_header', '--output_delimiter=,',
        '-q', query, '-o', output_file
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        logging.info(f"SUCCESS: Successfully exported data to {output_file}")
        logging.debug(stdout.decode()) 
        return True
    else:
        logging.error(f"ERROR: Impala command failed for output file {output_file}.")
        
        stderr_decoded = stderr.decode()
        erro_classificado = classificar_erro_impala(stderr_decoded)
        logging.warning(f"Mapped Error: {erro_classificado['categoria']}")
        
        fatal_errors = ["TABLE_NOT_FOUND", "SYNTAX_ERROR", "AUTH_ERROR", "GENERIC_ERROR"]
        if erro_classificado['categoria'] in fatal_errors:
            logging.error(f"FATAL ERROR ({erro_classificado['categoria']}): Stopping retries.")
            logging.error(f"Error Details:\n{erro_classificado['detalhes']}")
            # Return True for fatal errors to stop the retry loop
            return True
            
        logging.warning(f"Transient error detected. Details: {stderr_decoded}")
        return False


def retry_loop(query_to_run: str, output_file: str, queues: list):
    """
    Manages the retry logic for exporting data.
    """
    logging.info(f"--- Starting export process for {output_file} ---")
    
    sucesso = False
    retry_cnt = 1
    while not sucesso:
        for fila in queues:
            try:
                query_string = f"set request_pool={fila}; set mem_limit=1000g; {query_to_run}" 
                logging.info(f"Attempting export with queue: {fila}")
                
                sucesso = run_export_on_impala(query_string, output_file)
                
                if sucesso:
                    break
            except Exception as e:
                logging.error(f"An unexpected script error occurred in queue {fila}: {e}") 
                time.sleep(2)
                continue
        
        if not sucesso:
            log_msg = (f"All queues failed for export job. "
                       f"Waiting 30 seconds before retrying (Attempt {retry_cnt}).") 
            logging.warning(log_msg)
            retry_cnt += 1
            time.sleep(30)
            
    logging.info(f"--- Finished export process for {output_file} ---")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """
    Main function to parse arguments and orchestrate the export process.
    """
    parser = argparse.ArgumentParser(
        description='Export Impala data to a raw CSV file with a retry mechanism.'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--table-name',
        dest='table_name',
        help='The full name of the Impala table to export (e.g., schema.tablename).'
    ) 
    group.add_argument(
        '--query-file',
        dest='query_file',
        help='Path to a file containing the SQL SELECT query to execute and export.'
    )
    parser.add_argument(
        '--output-file',
        dest='output_file',
        required=True,
        help='The full path for the output CSV file (e.g., /path/to/output.csv). Compression must be handled by the caller.'
    )
    args = parser.parse_args() 

    # Determine the query to run based on arguments
    query_to_run = ""
    if args.table_name:
        logging.info(f"Mode: Exporting table '{args.table_name}'")
        query_to_run = f"select * from {args.table_name};"
    elif args.query_file:
        logging.info(f"Mode: Executing query from file '{args.query_file}'")
        try:
            with open(args.query_file, 'r') as f:
                query_to_run = f.read()
            if not query_to_run.strip():
                logging.error(f"ERROR: The provided query file '{args.query_file}' is empty.")
                sys.exit(1)
        except FileNotFoundError:
            logging.error(f"ERROR: The query file '{args.query_file}' was not found.")
            sys.exit(1)

    filas = ["adhoc_fast", "adhoc_small", "adhoc"] 

    logging.info("--- Script Configuration ---")
    logging.info(f"Output CSV file: {args.output_file}")
    logging.info("--------------------------")

    retry_loop(query_to_run, args.output_file, filas)

    logging.info(f"Export job for {args.output_file} is complete.")


if __name__ == '__main__':
    main()