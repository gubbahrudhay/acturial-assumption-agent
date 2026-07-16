import os

def replace_prints_in_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    new_lines = []
    has_logger_import = False
    for line in lines:
        if "from logger import get_logger" in line:
            has_logger_import = True
            
        # Very basic print replacement
        if "print(" in line and "Exception" not in line:
            # Replace print with logger.info or logger.error
            # If it's in an except block or has 'Error', use error
            if "Error" in line or "Failed" in line:
                line = line.replace("print(", "logger.error(")
            else:
                line = line.replace("print(", "logger.info(")
        new_lines.append(line)
        
    if not has_logger_import:
        # Add import at top
        for i, line in enumerate(new_lines):
            if not line.startswith("import") and not line.startswith("from"):
                new_lines.insert(i, "import sys\nimport os\nsys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\nfrom logger import get_logger\nlogger = get_logger()\n")
                break
                
    with open(file_path, 'w') as f:
        f.writelines(new_lines)

files = [
    "backend/tools/validator.py",
    "backend/agent/investigation_agent.py",
    "backend/agent/copilot.py",
    "backend/agent/decision_logger.py",
    "backend/agent/business_impact_agent.py"
]

for f in files:
    if os.path.exists(f):
        replace_prints_in_file(f)
