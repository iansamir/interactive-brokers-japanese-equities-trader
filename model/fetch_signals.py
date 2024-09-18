import paramiko

def fetch_japanese_equities_file():
    # SFTP server details
    hostname = 'ftp-es02.alexability.com'
    port = 22
    username = 'ER100423'
    password = 'EWs9pa34KP'
    keyword = 'japanese_equities'
    local_filepath = 'raw_sentiment_news.csv.gz'  # Save the file to the current directory
    
    try:
        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to the server
        client.connect(hostname, username=username, password=password, port=port)

        # Open an SFTP session
        sftp = client.open_sftp()
        
        # List all files in the SFTP server's directory
        file_list = sftp.listdir()
        
        # Search for the file containing 'japanese_equities' in its name
        target_file = None
        for file in file_list:
            if keyword in file:
                target_file = file
                break
        
        if target_file:
            print(f"Found file: {target_file}")
            # Fetch the file from the server
            print("Attempting download...")
            sftp.get(target_file, local_filepath)
            print(f"File downloaded successfully and saved as {local_filepath}")
            return local_filepath 
        else:
            print(f"No file containing '{keyword}' found on the server.")
        
        # Close the SFTP connection
        sftp.close()
        client.close()

    except Exception as e:
        print(f"Error fetching the file: {e}")

if __name__ == "__main__":
    # Call the function to fetch the file
    fetch_japanese_equities_file()