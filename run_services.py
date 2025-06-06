#!/usr/bin/env python3
"""
Main runner for all independent core services.
Starts each service in its own process for true independence.
"""
import asyncio
import subprocess
import sys
import os
import signal
import logging
from pathlib import Path
from typing import Dict, List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceManager:
    """Manages multiple independent services"""
    
    def __init__(self, config_file: str = "services_config.json"):
        self.config_file = config_file
        self.services = {}
        self.processes = {}
        self.running = False
    
    def load_config(self):
        """Load services configuration"""
        config_path = Path(__file__).parent / self.config_file
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.services = json.load(f)
        else:
            # Default configuration
            self.services = {
                "engines": {
                    "path": "engines/run_engines.py",
                    "port": 8001,
                    "enabled": True
                },
                "llm-council": {
                    "path": "llm-council/run_council.py", 
                    "port": 8002,
                    "enabled": True
                },
                "packages": {
                    "path": "packages/run_packages.py",
                    "port": 8003,
                    "enabled": True
                },
                "rag": {
                    "path": "rag/run_rag.py",
                    "port": 8004,
                    "enabled": True
                }
            }
            self.save_config()
    
    def save_config(self):
        """Save current configuration"""
        config_path = Path(__file__).parent / self.config_file
        with open(config_path, 'w') as f:
            json.dump(self.services, f, indent=2)
    
    async def start_service(self, service_name: str, service_config: Dict):
        """Start a single service"""
        if not service_config.get('enabled', True):
            logger.info(f"Service {service_name} is disabled")
            return
        
        service_path = Path(__file__).parent / service_config['path']
        
        if not service_path.exists():
            logger.error(f"Service script not found: {service_path}")
            return
        
        logger.info(f"Starting service: {service_name}")
        
        env = os.environ.copy()
        env['SERVICE_NAME'] = service_name
        env['SERVICE_PORT'] = str(service_config['port'])
        
        try:
            process = subprocess.Popen([
                sys.executable, str(service_path)
            ], env=env)
            
            self.processes[service_name] = process
            logger.info(f"Service {service_name} started with PID: {process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
    
    async def start_all_services(self):
        """Start all enabled services"""
        logger.info("Starting all core services...")
        
        for service_name, service_config in self.services.items():
            await self.start_service(service_name, service_config)
            await asyncio.sleep(2)  # Give each service time to start
        
        self.running = True
        logger.info("All services started")
    
    def stop_service(self, service_name: str):
        """Stop a single service"""
        if service_name in self.processes:
            process = self.processes[service_name]
            logger.info(f"Stopping service: {service_name}")
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing service: {service_name}")
                process.kill()
            
            del self.processes[service_name]
    
    def stop_all_services(self):
        """Stop all running services"""
        logger.info("Stopping all services...")
        
        for service_name in list(self.processes.keys()):
            self.stop_service(service_name)
        
        self.running = False
        logger.info("All services stopped")
    
    def check_services(self):
        """Check status of all services"""
        for service_name, process in self.processes.items():
            if process.poll() is None:
                logger.info(f"Service {service_name}: Running (PID: {process.pid})")
            else:
                logger.error(f"Service {service_name}: Stopped (Exit code: {process.returncode})")
    
    async def run(self):
        """Main service manager loop"""
        self.load_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        await self.start_all_services()
        
        # Monitor services
        try:
            while self.running:
                await asyncio.sleep(30)  # Check every 30 seconds
                self.check_services()
                
                # Restart failed services
                for service_name, service_config in self.services.items():
                    if service_name in self.processes:
                        process = self.processes[service_name]
                        if process.poll() is not None:  # Process has died
                            logger.warning(f"Service {service_name} died, restarting...")
                            del self.processes[service_name]
                            await self.start_service(service_name, service_config)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop_all_services()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False

async def main():
    """Main entry point"""
    manager = ServiceManager()
    await manager.run()

if __name__ == "__main__":
    asyncio.run(main())
