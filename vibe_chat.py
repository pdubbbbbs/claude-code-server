#!/usr/bin/env python3
"""
Vibe Chat - Natural language AI coding assistant
Integrates Claude Code Server and GitHub Copilot for interactive coding conversations
"""

import asyncio
import sys
from typing import Optional
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

console = Console()

CLAUDE_BASE_URL = "http://localhost:8002"
COMMANDS = {
    "/claude": "Switch to Claude AI",
    "/copilot": "Switch to GitHub Copilot (via suggest)",
    "/help": "Show this help",
    "/quit": "Exit vibe chat",
    "/clear": "Clear screen"
}


class VibeChat:
    def __init__(self):
        self.current_ai = "claude"
        self.conversation_history = []
        
    async def send_to_claude(self, message: str, stream: bool = True) -> str:
        """Send message to Claude Code Server"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{CLAUDE_BASE_URL}/chat",
                    json={
                        "message": message,
                        "stream": stream,
                        "system_prompt": "You are a helpful coding assistant. Provide clear, concise answers with code examples when relevant."
                    }
                )
                
                if stream:
                    # For now, return non-streaming. Streaming would need SSE parsing
                    pass
                
                if response.status_code == 200:
                    return response.text
                else:
                    return f"Error: Claude server returned {response.status_code}"
        except httpx.ConnectError:
            return "❌ Cannot connect to Claude Code Server. Is it running on localhost:8002?"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def send_to_copilot(self, message: str) -> str:
        """Send message to GitHub Copilot CLI"""
        try:
            # Use gh copilot suggest for command generation
            proc = await asyncio.create_subprocess_shell(
                f'gh copilot suggest "{message}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return stdout.decode()
            else:
                error = stderr.decode()
                return f"❌ Copilot error: {error if error else 'Unknown error'}"
        except Exception as e:
            return f"❌ Error calling gh copilot: {str(e)}"
    
    def show_help(self):
        """Display help information"""
        help_text = "\n".join([f"  {cmd}: {desc}" for cmd, desc in COMMANDS.items()])
        console.print(Panel(
            f"[bold cyan]Vibe Chat Commands[/bold cyan]\n\n{help_text}\n\n"
            f"[dim]Currently using: {self.current_ai.upper()}[/dim]",
            border_style="cyan"
        ))
    
    def display_message(self, role: str, content: str):
        """Display a chat message with formatting"""
        if role == "user":
            console.print(f"\n[bold green]You:[/bold green] {content}")
        elif role == "assistant":
            console.print(f"\n[bold blue]{self.current_ai.upper()}:[/bold blue]")
            try:
                # Try to render as markdown
                console.print(Markdown(content))
            except Exception:
                # Fallback to plain text
                console.print(content)
    
    async def process_message(self, message: str) -> bool:
        """Process user message and return False if should quit"""
        message = message.strip()
        
        # Handle commands
        if message.startswith("/"):
            cmd = message.lower()
            
            if cmd == "/quit" or cmd == "/q":
                return False
            elif cmd == "/help" or cmd == "/h":
                self.show_help()
            elif cmd == "/claude":
                self.current_ai = "claude"
                console.print("[cyan]✓ Switched to Claude AI[/cyan]")
            elif cmd == "/copilot":
                self.current_ai = "copilot"
                console.print("[cyan]✓ Switched to GitHub Copilot[/cyan]")
            elif cmd == "/clear":
                console.clear()
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]")
            
            return True
        
        # Skip empty messages
        if not message:
            return True
        
        # Display user message
        self.display_message("user", message)
        
        # Get AI response
        with console.status(f"[cyan]Thinking with {self.current_ai}...[/cyan]"):
            if self.current_ai == "claude":
                response = await self.send_to_claude(message, stream=False)
            else:
                response = await self.send_to_copilot(message)
        
        # Display AI response
        self.display_message("assistant", response)
        
        # Store in history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return True
    
    async def run(self):
        """Main chat loop"""
        console.clear()
        console.print(Panel.fit(
            "[bold magenta]🎵 Vibe Chat[/bold magenta]\n"
            "Natural language coding with Claude & Copilot\n\n"
            "[dim]Type /help for commands[/dim]",
            border_style="magenta"
        ))
        
        # Check Claude server
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.get(f"{CLAUDE_BASE_URL}/health")
            console.print("[green]✓ Claude Code Server connected[/green]")
        except:
            console.print("[yellow]⚠ Claude Code Server not available (start with: python server.py)[/yellow]")
        
        console.print(f"[cyan]Starting with: {self.current_ai.upper()}[/cyan]\n")
        
        # Main loop
        while True:
            try:
                message = Prompt.ask("\n[bold cyan]>>[/bold cyan]")
                should_continue = await self.process_message(message)
                
                if not should_continue:
                    console.print("\n[magenta]👋 Peace out! Keep vibing![/magenta]")
                    break
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Use /quit to exit[/yellow]")
            except EOFError:
                break


async def main():
    chat = VibeChat()
    await chat.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[magenta]Goodbye![/magenta]")
        sys.exit(0)
