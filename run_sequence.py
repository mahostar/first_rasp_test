import subprocess
import sys
import time

def run_script(script_name):
    """Run a Python script and return True if successful, False otherwise"""
    print(f"\n{'='*50}")
    print(f"Running {script_name}...")
    print(f"{'='*50}\n")
    
    try:
        # Run the script and capture output
        process = subprocess.run(
            [sys.executable, script_name],
            check=True,
            text=True,
            capture_output=True
        )
        
        # Print the output
        if process.stdout:
            print(process.stdout)
        if process.stderr:
            print(process.stderr)
            
        print(f"\n✅ {script_name} completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running {script_name}:")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("\nOutput:")
            print(e.stdout)
        if e.stderr:
            print("\nError:")
            print(e.stderr)
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error running {script_name}:")
        print(str(e))
        return False

def main():
    # Define the sequence of scripts
    scripts = [
        "image_grabber.py",
        "embedding_generator.py",
        "face_scanner.py"
    ]
    
    print("\n🚀 Starting script sequence...")
    
    # Run each script in sequence
    for script in scripts:
        # Add a small delay between scripts
        time.sleep(1)
        
        # Run the script
        success = run_script(script)
        
        # If the script failed, stop the sequence
        if not success:
            print(f"\n❌ Sequence stopped due to error in {script}")
            sys.exit(1)
    
    print("\n✨ All scripts completed successfully!")

if __name__ == "__main__":
    main() 