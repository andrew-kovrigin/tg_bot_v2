#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Telegram bot application.
"""
import sys
import os
import argparse
import asyncio

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Telegram bot application')
    parser.add_argument('--mode', choices=['bot', 'admin', 'both'], default='both',
                        help='Mode to run: bot, admin, or both (default)')
    
    args = parser.parse_args()
    
    if args.mode == 'bot':
        # Import and run the main bot
        from handlers.main import main
        asyncio.run(main())
    elif args.mode == 'admin':
        # Import and run the admin panel
        import admin
        admin.app.run(host='127.0.0.1', port=5000, debug=True)
    else:  # both
        # For simplicity, we'll just start the bot in this example
        # In a real application, you might want to run both in separate processes
        from handlers.main import main
        asyncio.run(main())