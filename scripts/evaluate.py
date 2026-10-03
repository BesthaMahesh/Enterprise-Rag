import os
import sys

# Forward to evaluate_rag.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.evaluate_rag import main

if __name__ == "__main__":
    main()
