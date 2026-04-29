import re

def clean_wrappers(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to match basic super() wrappers
    # Example:
    #     def check_win(self, *args, **kwargs):
    #         return super().check_win(*args, **kwargs)
    
    pattern = re.compile(
        r"^[ \t]+def\s+[a-zA-Z0-9_]+\s*\(\s*self\s*,\s*\*args\s*,\s*\*\*kwargs\s*\)\s*:\s*\n"
        r"[ \t]+return\s+super\(\)\.[a-zA-Z0-9_]+\s*\(\s*\*args\s*,\s*\*\*kwargs\s*\)\s*\n",
        re.MULTILINE
    )
    
    new_content, count = pattern.subn('', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Removed {count} wrappers from {filepath}")

if __name__ == '__main__':
    clean_wrappers('iqoptionapi/stable_api.py')
