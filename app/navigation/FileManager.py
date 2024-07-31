import os
import platform
import subprocess

class FileManager:
    """ Utility class to interact with files. """

    @staticmethod
    def open_file(file_name):
        current_os = platform.system()
        try:
            if current_os == 'Darwin': # macOS
                subprocess.run(['open', file_name], check=True)
            elif current_os == 'Windows':
                os.startfile(file_name) # pylint: disable=no-member
            elif current_os == 'Linux':
                subprocess.run(['xdg-open', file_name], check=True)
            else:
                raise ValueError("Unsupported operating system")
        except Exception: # pylint: disable=broad-exception-caught
            print(f"Please open the file: {file_name} to check the results.")
        
    @staticmethod
    def delete_files_by_extension(extension):
        current_dir = os.getcwd()
        for file in os.listdir(current_dir):
            if file.endswith(extension):
                file_path = os.path.join(current_dir, file)
                os.remove(file_path)