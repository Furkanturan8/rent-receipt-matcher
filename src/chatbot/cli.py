#!/usr/bin/env python3
"""
Chatbot CLI Interface

Interactive command-line interface for the real estate chatbot.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.chatbot import RealEstateChatbot


class ChatbotCLI:
    """Interactive CLI for chatbot."""
    
    def __init__(self, mock_db_path: Optional[str] = None):
        """Initialize CLI."""
        self.chatbot = RealEstateChatbot(mock_db_path=mock_db_path)
        self.running = False
    
    def print_separator(self, char="=", length=80):
        """Print separator line."""
        print(char * length)
    
    def print_message(self, message: str, prefix: str = ""):
        """Print formatted message."""
        if prefix:
            print(f"{prefix} {message}")
        else:
            print(message)
    
    def start(self):
        """Start interactive chat session."""
        self.running = True
        
        # Welcome message
        self.print_separator()
        print(self.chatbot.get_welcome_message())
        self.print_separator()
        print()
        
        while self.running:
            try:
                # Get user input
                user_input = input("👤 Siz: ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['çıkış', 'exit', 'quit', 'q']:
                    print()
                    print(self.chatbot.templates.GOODBYE)
                    self.running = False
                    break
                
                # Check for file upload (PDF path)
                if user_input.endswith('.pdf') and Path(user_input).exists():
                    self.process_receipt(user_input)
                
                # Regular message
                else:
                    response = self.chatbot.handle_message(user_input)
                    print()
                    print("🤖 Bot:", response)
                    print()
            
            except KeyboardInterrupt:
                print("\n")
                print(self.chatbot.templates.GOODBYE)
                self.running = False
                break
            
            except Exception as e:
                print(f"\n❌ Hata: {e}\n")
    
    def process_receipt(self, pdf_path: str):
        """Process receipt PDF."""
        print()
        print(f"📄 Dekont işleniyor: {pdf_path}")
        print("⏳ Lütfen bekleyin...")
        print()
        
        result = self.chatbot.process_receipt(pdf_path)
        
        if result['success']:
            print("🤖 Bot:")
            print(result['response'])
        else:
            print(f"❌ Hata: {result.get('error', 'Bilinmeyen hata')}")
        
        print()
    
    def run_demo(self):
        """Run demo conversation."""
        print()
        self.print_separator("=")
        print("🎬 DEMO MOD")
        self.print_separator("=")
        print()
        
        # Demo scenarios
        scenarios = [
            {
                "description": "Merhaba mesajı",
                "input": "Merhaba",
            },
            {
                "description": "Yardım menüsü",
                "input": "yardım",
            },
            {
                "description": "Kiracı bilgisi sorgulama",
                "input": "Furkan Turan bilgilerini göster",
            },
            {
                "description": "Bilinmeyen komut",
                "input": "Bugün hava nasıl?",
            },
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*80}")
            print(f"Senaryo {i}: {scenario['description']}")
            print(f"{'='*80}\n")
            
            print(f"👤 Siz: {scenario['input']}")
            response = self.chatbot.handle_message(scenario['input'])
            print(f"\n🤖 Bot: {response}\n")
            
            input("Enter tuşuna basarak devam edin...")
        
        print("\n" + "="*80)
        print("✅ Demo tamamlandı!")
        print("="*80 + "\n")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real Estate Chatbot CLI")
    parser.add_argument(
        '--pdf',
        type=str,
        help='Process a receipt PDF file'
    )
    parser.add_argument(
        '--mock-db',
        type=str,
        default='tests/mock-data.json',
        help='Path to mock database JSON file'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run demo conversation'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='Start interactive chat session (default)'
    )
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = ChatbotCLI(mock_db_path=args.mock_db)
    
    # Run mode
    if args.pdf:
        # Process single PDF
        cli.process_receipt(args.pdf)
    
    elif args.demo:
        # Run demo
        cli.run_demo()
    
    else:
        # Interactive mode
        cli.start()


if __name__ == '__main__':
    main()
