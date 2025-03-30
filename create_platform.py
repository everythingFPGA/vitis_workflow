# Andrea Bizzotto

# place the script in the root folder of your Vitis workspace and run it with: 
#   vitis -s create_platform.py

# TODO enable the library in the platform
# TODO create a system project
# TODO handle multiple platforms

#%%
import os
import xml.etree.ElementTree as ET
import vitis
#import hsi # to read information out of the .xsa 

# try to import tkinter for the file dialog
try:
    from tkinter import tk
    from tkinter import filedialog
    tk_exists = True
except ImportError:
    print("tkinter is not available. File dialog will not be used.")
    print("run the python installer and mark the TK box to install it.")

#%%
def find_file_by_extension(extension, directory="."):
    print("Looking for '{extension}' file...")
    file_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                file_paths.append(os.path.join(root, file))
    if not file_paths:
        print(f"No files with extension '{extension}' found.")

        if tk_exists:
            print("Please select the file manually.")
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            
            file_path = filedialog.askopenfilename(title=f"Select a '{extension}' file", filetypes=[("Files", "*"+extension)])
            
            if not file_path:
                print("No file selected.")
                return
        else:
            file_path = input("Please enter the full path to the '{extension}' file: ")
            
    else:
        print(f"Found {len(file_paths)} files with extension '{extension}'")
        if len(file_paths) == 1:
            file_path = file_paths[0]
        else:
            print("Choose one of the files:")
            for i, file_path in enumerate(file_paths):
                print(f"[{i}]: {file_path}")
            choice = input("Enter the number of the file you want to use: ")
            try:
                choice = int(choice)
                if choice < 0 or choice >= len(file_paths):
                    print("Invalid choice. Using the first file.")
                    choice = 0
            except ValueError:
                print("Invalid input. Using the first file.")
                choice = 0
            file_path = file_paths[choice]

    return file_path

#%%
def extract_spfm_info():
    """Finds and extracts CPU and domain information from a .spfm XML file."""
    
    # Step 1: Locate the .spfm file
    spfm_path = find_file_by_extension(".spfm")

    # Step 2: Load and parse the XML file
    print("Extracting information from .spfm file...")
    try:
        tree = ET.parse(spfm_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print("Error parsing the XML file:", e)
        return
    except FileNotFoundError:
        print("The specified .spfm file was not found.")
        return

    # Define XML Namespace
    ns = {"sdx": "http://www.xilinx.com/sdx"}

    # Extract platform name
    platform_name = root.attrib.get("sdx:name", "Unknown Platform")

    # Extract CPU instances and domain names
    cpu_list = []
    domain_list = []

    for processor in root.findall(".//sdx:processorGroup", ns):
        cpu_instance = processor.attrib.get("sdx:cpuInstance")
        domain_name = processor.attrib.get("sdx:name")
        
        if cpu_instance and domain_name:
            cpu_list.append(cpu_instance)
            domain_list.append(domain_name)

    # Step 3: Validate and print results
    if not cpu_list:
        print("No CPU list found in the .spfm file.")
        return
    if not domain_list:
        print("No Domain list found in the .spfm file.")
        return

    print("--------------------------------------")
    print("Platform Name:", platform_name)
    print("CPU List:", cpu_list)
    print("Domain List:", domain_list)
    print("--------------------------------------")

    return platform_name, cpu_list, domain_list

#%%
def main():
    #%% Get the current working directory
    workspace_path = os.getcwd()

    # Create the client
    client = vitis.create_client()

    if client.check_workspace():
        print("Setting Vitis workspace...")
        client.set_workspace(workspace_path)
    else:
        print("Warning: Not a Vitis workspace")
        print("Updating to a Vitis workspace...")
        print("Seting Vitis workspace...")
        client.update_workspace(workspace_path)
        client.set_workspace(workspace_path)
    
    
    platform_name, cpu_list, domain_list = extract_spfm_info()

    #%% get the xsa path
    print("Looking for .xsa file...")
    xsa_path = find_file_by_extension(".xsa")

    if not xsa_path:
        print("No .xsa file found.")
        xsa_path = input("Please enter the full path to the .xsa file: ")
    else:
        xsa_path = xsa_path[0]
        print("Found .xsa file: ", xsa_path)

    #%% Create the platform
    print("Creating platform...")
    platform = client.create_platform_component(name = platform_name, hw_design = xsa_path, os = "standalone",cpu = cpu_list[0], domain_name = domain_list[0])
    print("Platform Created: ", platform_name)

    #%% create a domain, for each domain in the list
    print("Creating domains...")
    for i in range(0, len(domain_list)):
        domain = platform.add_domain(cpu = cpu_list[i], os = "standalone", name = domain_list[i], display_name = domain_list[i])
        print("Domain Created: ", domain_list[i])

    #%% build platform
    print("Building platform...")
    platform = client.get_component(platform_name)
    status = platform.build()
    if status == "SUCCESS":
        print("Platform build success.")
    else:
        print("Platform build status: ", status)
    
    #%% create application
    # client.create_app_component(name, platform, domain=None, cpu=None, os=None, template=None)
    # no need to create an application project, just keep the file: vitis-comp.json and src

    #%% create system project
    # client.create_sys_project(name, platform)

    #%%
    client.close()

    #run the system command to open vitis in this folder
    print("Opening Vitis...")
    os.system("vitis -w " + workspace_path)

if __name__ == "__main__":
    main()
