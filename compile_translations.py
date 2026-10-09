import os
import subprocess
import sys

def compile_translations():
    """Compile all translation files."""
    try:
        # Skip compilation in serverless environments like Vercel
        if os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
            print("Skipping translation compilation in serverless environment")
            return True
            
        # Get the absolute path to the translations directory
        translations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'translations')
        
        if not os.path.exists(translations_dir):
            print(f"Translations directory not found at {translations_dir}")
            return True  # Return True to not fail the app startup

        # Check if pybabel is available
        try:
            subprocess.run(['pybabel', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("pybabel not available - skipping translation compilation")
            return True  # Return True to not fail the app startup

        # Compile translations for each language
        for lang in os.listdir(translations_dir):
            lang_dir = os.path.join(translations_dir, lang)
            if os.path.isdir(lang_dir):
                po_file = os.path.join(lang_dir, 'LC_MESSAGES', 'messages.po')
                if os.path.exists(po_file):
                    print(f"Compiling translations for {lang}...")
                    try:
                        subprocess.run(['pybabel', 'compile', '-d', translations_dir], check=True)
                        print(f"Successfully compiled translations for {lang}")
                    except subprocess.CalledProcessError as e:
                        print(f"Error compiling translations for {lang}: {str(e)}")
                        continue
        
        print("Translation compilation completed!")
    except Exception as e:
        print(f"Error in translation compilation: {str(e)}")
        # Don't raise the exception, just log it
        return True  # Return True to not fail the app startup
    return True

if __name__ == '__main__':
    compile_translations() 