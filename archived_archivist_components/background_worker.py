"""
Background worker for embedding generation, knowledge graph updates, and reconciliation.
"""
import threading
import time
import logging
import asyncio
from .unified_storage import UnifiedStorageLayer
from .brain.memory import MemorySystem
from .brain.knowledge import KnowledgeManager
from .brain.reasoning import ReasoningEngine
from .enhanced_event_bus import EventBus
from prometheus_client import Counter, Histogram, Gauge, start_http_server

logger = logging.getLogger(__name__)

# Prometheus metrics
EMBEDDINGS_GENERATED = Counter('archivist_embeddings_generated', 'Number of embeddings generated')
GRAPH_UPDATES = Counter('archivist_graph_updates', 'Number of graph updates')
RECONCILIATIONS = Counter('archivist_reconciliations', 'Number of data reconciliations')
ERRORS = Counter('archivist_background_worker_errors', 'Number of errors in background worker')
LAST_RUN_STATUS = Gauge('archivist_background_worker_last_status', 'Last run status (1=success, 0=error)')
EMBEDDING_DURATION = Histogram('archivist_embedding_duration_seconds', 'Duration of embedding generation')
GRAPH_UPDATE_DURATION = Histogram('archivist_graph_update_duration_seconds', 'Duration of graph update')
RECONCILIATION_DURATION = Histogram('archivist_reconciliation_duration_seconds', 'Duration of reconciliation')

class BackgroundWorker:
    def __init__(self):
        self.running = False
        self.storage = UnifiedStorageLayer()
        self.memory = MemorySystem()
        self.knowledge = KnowledgeManager()
        self.reasoning = ReasoningEngine()
        self.event_bus = EventBus()
        self.metrics = {
            'embeddings_generated': 0,
            'graph_updates': 0,
            'reconciliations': 0,
            'errors': 0
        }
        self.last_run = None
        self.last_status = "never_run"
        self.last_error = None
        self.operation_timings = {
            'embeddings': [],
            'graph_updates': [],
            'reconciliations': []
        }

    @property
    def health(self):
        return {
            'running': self.running,
            'last_run': self.last_run,
            'last_status': self.last_status,
            'last_error': self.last_error,
            'metrics': self.metrics,
            'operation_timings': {k: v[-5:] for k, v in self.operation_timings.items()}
        }

    def start(self, metrics_port: int = 8001):
        self.running = True
        # Start Prometheus metrics server
        start_http_server(metrics_port)
        loop = asyncio.get_event_loop()
        loop.create_task(self.run_async())

    async def run_async(self):
        while self.running:
            self.last_run = time.time()
            try:
                with EMBEDDING_DURATION.time():
                    t0 = time.time()
                    await self._generate_embeddings_async()
                    self.operation_timings['embeddings'].append(time.time() - t0)
                with GRAPH_UPDATE_DURATION.time():
                    t1 = time.time()
                    await self._update_graph_db_async()
                    self.operation_timings['graph_updates'].append(time.time() - t1)
                with RECONCILIATION_DURATION.time():
                    t2 = time.time()
                    await self._reconcile_data_async()
                    self.operation_timings['reconciliations'].append(time.time() - t2)
                self.last_status = "success"
                self.last_error = None
                LAST_RUN_STATUS.set(1)
                logger.info(f"BackgroundWorker metrics: {self.metrics}")
            except Exception as e:
                logger.error(f"BackgroundWorker error: {e}")
                self.metrics['errors'] += 1
                ERRORS.inc()
                self.last_status = "error"
                self.last_error = str(e)
                LAST_RUN_STATUS.set(0)
            await asyncio.sleep(10)

    async def _generate_embeddings_async(self):
        try:
            items = await self.storage.get_items_missing_embeddings(limit=10)
            for item in items:
                embedding = await self.memory._generate_embedding(item['content'])
                await self.storage.update_embedding(item['id'], embedding)
                self.metrics['embeddings_generated'] += 1
                EMBEDDINGS_GENERATED.inc()
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            self.metrics['errors'] += 1
            ERRORS.inc()

    async def _update_graph_db_async(self):
        try:
            updates = await self.knowledge.get_pending_graph_updates(limit=10)
            for update in updates:
                await self.knowledge.apply_graph_update(update)
                self.metrics['graph_updates'] += 1
                GRAPH_UPDATES.inc()
        except Exception as e:
            logger.error(f"Graph DB update error: {e}")
            self.metrics['errors'] += 1
            ERRORS.inc()

    async def _reconcile_data_async(self):
        try:
            duplicates = await self.memory.find_duplicates(limit=5)
            for dup in duplicates:
                await self.memory.merge_duplicates(dup)
                self.metrics['reconciliations'] += 1
                RECONCILIATIONS.inc()
            await self.memory._cleanup_old_memories()
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
            self.metrics['errors'] += 1
            ERRORS.inc()
