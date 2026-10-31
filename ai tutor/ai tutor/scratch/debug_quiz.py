import sys
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.quiz_generator import generate_quiz
from app.database.db import SessionLocal

def test_quiz():
    db = SessionLocal()
    topic = "ensemble learning"
    user_id = "tester_123"
    
    print(f"Testing quiz generation for topic: {topic}")
    result = generate_quiz(topic=topic, user_id=user_id, db=db, num_questions=5)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Success! Generated {len(result['questions'])} questions.")
        for i, q in enumerate(result['questions']):
            print(f"{i+1}. {q['question']}")

if __name__ == "__main__":
    test_quiz()
