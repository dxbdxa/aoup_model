from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from legacy.simcore.catalog import TaskCatalog
from legacy.simcore.models import SimulationTask

from src.adapters.legacy_simcore_adapter import legacy_task_point_to_run_config
from src.configs.schema import SweepTask


class LegacyCatalogUnavailableError(RuntimeError):
    pass


class CatalogBridge:
    """Translate legacy catalog tasks into the new workflow schema."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)

    def load_catalog(self) -> TaskCatalog:
        try:
            return TaskCatalog(self.project_root)
        except FileNotFoundError as exc:
            raise LegacyCatalogUnavailableError(
                "Legacy TaskCatalog requires external Experiment design files that are not present in this checkout."
            ) from exc

    def list_sweep_tasks(self) -> list[SweepTask]:
        catalog = self.load_catalog()
        return [self.legacy_task_to_sweep_task(task, batch_index=index) for index, task in enumerate(catalog.list_tasks())]

    def get_sweep_task(self, task_id: str, *, batch_index: int = 0) -> SweepTask:
        catalog = self.load_catalog()
        legacy_task = catalog.get(task_id)
        return self.legacy_task_to_sweep_task(legacy_task, batch_index=batch_index)

    @staticmethod
    def legacy_task_to_sweep_task(legacy_task: SimulationTask, *, batch_index: int = 0) -> SweepTask:
        configs = tuple(legacy_task_point_to_run_config(legacy_task, point) for point in legacy_task.points)
        return SweepTask(
            task_id=legacy_task.task_id,
            phase=legacy_task.mode,
            batch_index=batch_index,
            config_list=configs,
            metadata={
                "legacy_run_id": legacy_task.run_id,
                "legacy_description": legacy_task.description,
                "legacy_notes": legacy_task.notes,
                "legacy_detectability_analysis": legacy_task.detectability_analysis,
            },
        )
