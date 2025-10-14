"""
Chat Terminal para Solverde.pt Chatbot
Interface de linha de comandos para conversar com o assistente
"""

import os
import sys
from datetime import datetime
from solverde_chatbot import SolverdeChatbot, FAQParser
import uuid
from dotenv import load_dotenv

# Desativar warning do tokenizers
os.environ["TOKENIZERS_PARALLELISM"] = "false"




class TerminalChat:
    """Interface de chat no terminal"""
    
    def __init__(self, chatbot: SolverdeChatbot):
        self.chatbot = chatbot
        self.session_id = str(uuid.uuid4())
        self.is_running = False
        
    def clear_screen(self):
        """Limpa o ecrã do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Imprime o cabeçalho do chat"""
        print("=" * 70)
        print("🎰 SOLVERDE.PT - ASSISTENTE VIRTUAL")
        print("=" * 70)
        print()
        print("Olá! Sou o assistente virtual do Solverde.pt.")
        print("Estou aqui para te ajudar com as tuas dúvidas.")
        print()
        print("Comandos especiais:")
        print("  /sair    - Terminar conversa")
        print("  /limpar  - Limpar histórico da conversa")
        print("  /novo    - Começar nova conversa")
        print("  /ajuda   - Mostrar comandos")
        print()
        print("=" * 70)
        print()
    
    def print_message(self, role: str, content: str):
        """
        Imprime uma mensagem formatada
        
        Args:
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
        """
        timestamp = datetime.now().strftime("%H:%M")
        
        if role == "user":
            print(f"\n[{timestamp}] 👤 Tu:")
            print(f"  {content}")
        else:
            print(f"\n[{timestamp}] 🤖 Assistente:")
            # Quebra linhas longas para melhor legibilidade
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    print(f"  {line}")
                else:
                    print()
        print()
    
    def print_thinking(self):
        """Mostra indicador de que o bot está a pensar"""
        print("🤔 A pensar...", end='\r')
    
    def handle_command(self, command: str) -> bool:
        """
        Processa comandos especiais
        
        Args:
            command: Comando do utilizador
            
        Returns:
            True se deve continuar, False se deve sair
        """
        command = command.lower().strip()
        
        if command == '/sair':
            print("\n👋 Obrigado por usar o assistente Solverde.pt!")
            print("Até breve!\n")
            return False
        
        elif command == '/limpar':
            self.chatbot.clear_conversation(self.session_id)
            self.clear_screen()
            self.print_header()
            print("✓ Histórico limpo! A conversa continua...\n")
            return True
        
        elif command == '/novo':
            self.session_id = str(uuid.uuid4())
            self.clear_screen()
            self.print_header()
            print("✓ Nova conversa iniciada!\n")
            return True
        
        elif command == '/ajuda':
            print("\n📋 COMANDOS DISPONÍVEIS:")
            print("  /sair    - Terminar e sair do chat")
            print("  /limpar  - Limpar histórico (mantém a sessão)")
            print("  /novo    - Começar conversa completamente nova")
            print("  /ajuda   - Mostrar esta mensagem")
            print()
            return True
        
        else:
            print(f"\n⚠ Comando desconhecido: {command}")
            print("  Use /ajuda para ver comandos disponíveis\n")
            return True
    
    def get_user_input(self) -> str:
        """
        Obtém input do utilizador com prompt colorido
        
        Returns:
            Input do utilizador
        """
        try:
            user_input = input("👤 Tu: ").strip()
            return user_input
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrompido. Até breve!")
            return '/sair'
        except EOFError:
            return '/sair'
    
    def run(self):
        """Inicia o loop principal do chat"""
        self.clear_screen()
        self.print_header()
        self.is_running = True
        
        # Primeira mensagem do bot
        print("🤖 Assistente:")
        print("  Como posso ajudar-te hoje?")
        print()
        
        while self.is_running:
            # Obter input do utilizador
            user_input = self.get_user_input()
            
            # Verificar se está vazio
            if not user_input:
                continue
            
            # Verificar se é comando
            if user_input.startswith('/'):
                should_continue = self.handle_command(user_input)
                if not should_continue:
                    self.is_running = False
                    break
                continue
            
            # Processar mensagem normal
            self.print_thinking()
            
            try:
                # Enviar para o chatbot
                response = self.chatbot.chat(self.session_id, user_input)
                
                # Limpar linha do "A pensar..."
                print(" " * 50, end='\r')
                
                # Mostrar resposta
                self.print_message("assistant", response)
                
            except Exception as e:
                print(" " * 50, end='\r')
                print(f"\n❌ Erro: {str(e)}")
                print("Por favor, tenta novamente.\n")


def main():
    """Função principal"""
    print("🚀 A inicializar o Assistente Solverde.pt...")
    print()

    load_dotenv()
    
    # 1. Obter API key da OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ ERRO: Variável de ambiente OPENAI_API_KEY não encontrada!")
        print()
        print("Por favor, define a tua API key:")
        print("  Linux/Mac: export OPENAI_API_KEY='sk-...'")
        print("  Windows: set OPENAI_API_KEY=sk-...")
        print()
        sys.exit(1)
    
    # 2. Inicializar chatbot
    try:
        chatbot = SolverdeChatbot(
            openai_api_key=api_key,
            persist_directory="./chroma_db"
        )
    except Exception as e:
        print(f"❌ Erro ao inicializar chatbot: {e}")
        sys.exit(1)
    
    # 3. Verificar se tem FAQs carregadas
    if chatbot.collection.count() == 0:
        print("⚠ Nenhuma FAQ encontrada na base de dados!")
        print()
        
        # Tentar carregar do caminho padrão
        default_faq_path = "docs/ajuda/perguntas_frequentes.md"
        
        if os.path.exists(default_faq_path):
            print(f"📁 A carregar FAQs de {default_faq_path}...")
            try:
                chatbot.load_faqs_from_file(default_faq_path)
            except Exception as e:
                print(f"❌ Erro ao carregar FAQs: {e}")
                sys.exit(1)
        else:
            # Perguntar caminho alternativo
            print(f"❌ Ficheiro não encontrado: {default_faq_path}")
            print()
            faq_file = input("Caminho alternativo para o ficheiro de FAQs (ou Enter para sair): ").strip()
            
            if not faq_file:
                print("Saindo...")
                sys.exit(0)
            
            if not os.path.exists(faq_file):
                print(f"❌ Ficheiro não encontrado: {faq_file}")
                sys.exit(1)
            
            print(f"📁 A carregar FAQs de {faq_file}...")
            try:
                chatbot.load_faqs_from_file(faq_file)
            except Exception as e:
                print(f"❌ Erro ao carregar FAQs: {e}")
                sys.exit(1)
    
    print("✓ Chatbot pronto!")
    print()
    input("Pressiona Enter para começar...")
    
    # 4. Iniciar interface de chat
    terminal_chat = TerminalChat(chatbot)
    terminal_chat.run()


if __name__ == "__main__":
    main()