#!/usr/bin/env python3
"""
Test script for the hybrid intent classification system
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bitzapp.settings')
django.setup()

from chatbot.intent_classifier import IntentClassifier

def test_hybrid_classifier():
    """
    Test the hybrid intent classification system
    """
    classifier = IntentClassifier()
    
    # Test cases
    test_cases = [
        # Simple slash commands (regex)
        "/create",
        "/balance", 
        "/deposit 5000",
        
        # Simple regex patterns
        "create wallet",
        "check balance",
        "deposit 2000 naira",
        
        # Complex natural language (Gemini)
        "I'd like to open a Bitcoin wallet please",
        "Can you help me send some Bitcoin to my friend John?",
        "I want to convert 5000 naira to Bitcoin",
        "What's the current status of my Bitcoin holdings?",
        "How can I withdraw my Bitcoin to my bank account?",
        
        # Chat questions
        "What is Bitcoin?",
        "How does Lightning Network work?",
        "Is Bitcoin secure?"
    ]
    
    print("🤖 Testing Hybrid Intent Classification System\n")
    print("=" * 60)
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{message}'")
        result = classifier.classify_intent(message)
        
        print(f"   Intent: {result['intent']}")
        if 'amount' in result:
            print(f"   Amount: {result['amount']}")
        if 'currency' in result:
            print(f"   Currency: {result['currency']}")
        if 'receiver' in result:
            print(f"   Receiver: {result['receiver']}")
        
        # Show which method was used
        if message.startswith('/'):
            print("   Method: Slash Command (Regex)")
        elif result['intent'] != 'chat':
            # Check if it was caught by regex first
            regex_result = classifier._classify_with_regex(message.lower())
            if regex_result['intent'] != 'chat':
                print("   Method: Regex Pattern Matching")
            else:
                print("   Method: Gemini AI Classification")
        else:
            print("   Method: Chat Response")
    
    print("\n" + "=" * 60)
    print("✅ Hybrid classification system test completed!")

if __name__ == "__main__":
    test_hybrid_classifier()
