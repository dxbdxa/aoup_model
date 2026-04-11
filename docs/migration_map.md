# Legacy Code Migration Map
Project: Active Transport / Productive Memory Workflow  
Status: Draft v1  
Owner: Xiaobin Dai  
Last updated: 2024-08-15

---

## 1. 迁移目标

本项目不以“重写旧代码”为目标，而以“在不破坏旧物理行为的前提下，将旧代码接入新的大规模扫描工作流”为目标。

迁移原则：

1. **旧物理内核优先保留**
2. **先包裹（wrap），后重构（refactor）**
3. **先回归一致，再做性能优化**
4. **新工作流负责调度、统计、归档和出图**
5. **旧代码负责单轨迹物理求值与底层几何/动力学计算**

---

## 2. 当前旧代码资产盘点

当前 legacy 代码库核心模块：

### 2.1 `legacy/simcore/simulation.py`
推测职责：
- 构建迷宫几何
- 构建导航势场 `psi`
- 构建 signed distance / wall normal 场
- 定义单粒子动力学推进器
- 执行单条轨迹模拟
- 输出首达、困陷、耗散等统计量

关键物理组成：
- active self-propulsion
- viscoelastic memory variable
- delayed feedback alignment
- uniform background flow
- soft wall repulsion
- first-passage detection

### 2.2 `legacy/simcore/catalog.py`
推测职责：
- 定义实验设计
- 定义参数扫描任务
- 定义图任务或批处理任务
- 组织不同 ablation（full / no_memory / no_feedback / no_flow）

### 2.3 几何与导航相关内部对象
在旧代码中隐含存在：
- `MazeBuilder`
- `NavigationSolver`
- distance / normal field builder
- 轨迹采样器 / PointSimulator

这些对象应尽量视为“可复用底层能力”，而不是立即改写。

---

## 3. 新工作流的目标结构

```text
project/
  docs/
    trae_active_transport_workflow.md
    migration_map.md

  legacy/
    simcore/
      simulation.py
      catalog.py
      ...

  src/
    adapters/
      legacy_simcore_adapter.py
      geometry_bridge.py
      catalog_bridge.py
    configs/
      schema.py
      defaults.yaml
      reference_cases.yaml
      coarse_scan.yaml
      refine_scan.yaml
    runners/
      run_single_case.py
      run_reference_scales.py
      run_benchmark_mini_scan.py
      run_coarse_scan.py
      run_adaptive_refine.py
    analysis/
      aggregate.py
      ridge_detection.py
      ranking_reversal.py
      collapse.py
    figures/
      fig1_phase_diagram.py
      fig2_speed_efficiency_split.py
      fig3_trapping_mechanism.py
      fig4_geometry_collapse.py
    utils/
      io.py
      seed.py
      hashing.py
      logging_utils.py

  tests/
    test_adapter_schema.py
    test_legacy_regression.py
    test_reference_scales.py
    test_small_scan_smoke.py

  outputs/
    runs/
    summaries/
    figures/
    logs/
```

---

## 4. 旧模块到新工作流模块的映射

| 旧模块 / 功能 | 物理角色 | 新模块位置 | 迁移方式 | 是否允许修改 |
| --- | --- | --- | --- | --- |
| `simulation.py` 主模拟入口 | 单轨迹求值核心 | `src/adapters/legacy_simcore_adapter.py` | 包裹调用 | 否，第一阶段不改 |
| `catalog.py` 参数任务组织 | 扫描设计入口 | `src/adapters/catalog_bridge.py` | 读取/翻译 | 否，第一阶段不改 |
| Maze geometry builder | 空间门控几何 | `src/adapters/geometry_bridge.py` | 复用/暴露接口 | 谨慎 |
| Navigation solver | 导航势场 | `src/adapters/geometry_bridge.py` | 复用/暴露接口 | 谨慎 |
| 单步推进 kernel | 动力学内核 | 暂留 legacy | 保持黑盒 | 否 |
| legacy 输出 dict | 原始结果格式 | `src/configs/schema.py` | 标准化转换 | 不直接依赖原格式 |
| 参数矩阵逻辑 | 旧实验定义 | `src/runners/*` | 逐步替代 | 是，新建替代层 |

---

## 5. 第一阶段不允许做的事

以下操作在 integration phase 1 禁止：

-   直接改写 `simulation.py` 的核心动力学更新公式
-   合并或删除旧代码文件
-   修改旧代码中的随机数逻辑
-   未做回归测试就改输出定义
-   未建立 adapter 就把旧入口替换成新入口
-   一上来把 legacy 改成并行版本

一句话：  
**先把旧代码接上新工作流，再谈重构。**



## 6. 第一阶段必须新增的文件
---------------

### 6.1 `src/configs/schema.py`

职责：

*   定义 `RunConfig`
*   定义 `RunResult`
*   定义 `SweepTask`
*   定义统一的 serialization schema

### 6.2 `src/adapters/legacy_simcore_adapter.py`

职责：

*   把 `RunConfig` 翻译为 legacy 参数
*   调用 legacy 单次运行
*   接收 legacy 输出
*   转换为 `RunResult`

### 6.3 `src/adapters/catalog_bridge.py`

职责：

*   从旧 catalog 中读取已有的实验设计
*   翻译为新 workflow 可识别的 task list
*   保留旧 ablation 标签

### 6.4 `tests/test_adapter_schema.py`

职责：

*   检查 adapter 输出字段完整性
*   检查 JSON / parquet / csv 可序列化性

### 6.5 `tests/test_legacy_regression.py`

职责：

*   对比 legacy 直跑与 adapter 包裹运行
*   检验关键指标一致性



## 7. 标准输入输出接口
------------

### 7.1 `RunConfig`

```
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class RunConfig:
    geometry_id: str
    model_variant: str   # full / no_memory / no_feedback / no_flow
    v0: float
    Dr: float
    tau_v: float
    gamma0: float
    gamma1: float
    tau_f: float
    U: float
    wall_thickness: float
    gate_width: float
    dt: float
    Tmax: float
    n_traj: int
    seed: int
    metadata: Optional[Dict] = None
```

### 7.2 `RunResult`

```
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class RunResult:
    run_id: str
    config_hash: str
    geometry_id: str
    model_variant: str

    p_succ: float
    mfpt_mean: Optional[float]
    mfpt_median: Optional[float]
    mfpt_q90: Optional[float]

    sigma_drag_mean: Optional[float]
    eta_sigma: Optional[float]

    trap_time_mean: Optional[float]
    trap_count_mean: Optional[float]
    wall_fraction_mean: Optional[float]
    revisit_rate_mean: Optional[float]

    n_traj: int
    n_success: int

    ci: Dict
    raw_summary_path: Optional[str]
    metadata: Dict
```

### 7.3 `SweepTask`

```
from dataclasses import dataclass
from typing import List

@dataclass
class SweepTask:
    task_id: str
    phase: str
    batch_index: int
    config_list: List[RunConfig]
```



## 8. 基准回归测试点
-----------

先固定 3–5 组 baseline cases：

### Case A: baseline reference

*   geometry = maze\_v1
*   model = full
*   low memory
*   low delay
*   no flow

### Case B: no memory control

*   geometry = maze\_v1
*   model = no\_memory
*   other parameters same as A

### Case C: no feedback control

*   geometry = maze\_v1
*   model = no\_feedback
*   other parameters same as A

### Case D: moderate productive-memory candidate

*   geometry = maze\_v1
*   moderate `tau_v`
*   moderate `tau_f`
*   moderate persistence

### Case E: strong-flow stress test

*   geometry = maze\_v1
*   large `U`
*   other parameters same as D

### 回归容差

*   `|ΔP_succ| < 0.02`
*   `relative error(MFPT) < 5%`
*   `relative error(eta_sigma) < 10%`



## 9. 融合步骤
--------

### Phase 0: Freeze legacy

*   将旧代码整体复制到 `legacy/simcore`
*   不修改物理内核
*   建立版本标签

### Phase 1: Interface mapping

*   识别 legacy 的单次运行入口
*   识别参数命名和默认值
*   识别输出字段
*   写成参数映射表

### Phase 2: Adapter wrapping

*   完成 `legacy_simcore_adapter.py`
*   能通过 `RunConfig` 调用 legacy
*   能返回 `RunResult`

### Phase 3: Regression lock

*   跑 3–5 个 baseline cases
*   建立 regression tests
*   锁定数值行为

### Phase 4: Workflow injection

*   用 adapter 接入：
    *   reference scales
    *   benchmark mini-scan
    *   coarse scan

### Phase 5: Structured output

*   将所有运行结果落盘到统一目录
*   统一 hash / seed / metadata

### Phase 6: Selective refactor

仅在以下条件满足后允许：

*   adapter 稳定
*   regression 通过
*   已识别真实性能瓶颈



## 10. legacy 参数到新 schema 的映射表
----------------------------

> 这一节需要在 agent 首轮阅读后自动补全

| 新字段 | legacy 参数名 | 来源文件 | 默认值 | 备注 |
| --- | --- | --- | --- | --- |
| `v0` | TBD | `simulation.py` | TBD | 自推进速度 |
| `Dr` | TBD | `simulation.py` | TBD | 旋转扩散 |
| `tau_v` | TBD | `simulation.py` | TBD | 记忆松弛时间 |
| `gamma0` | TBD | `simulation.py` | TBD | 瞬时摩擦 |
| `gamma1` | TBD | `simulation.py` | TBD | 记忆强度 |
| `tau_f` | TBD | `simulation.py` | TBD | 反馈延迟 |
| `U` | TBD | `simulation.py` | TBD | 外部流速 |
| `dt` | TBD | `simulation.py` | TBD | 时间步长 |
| `Tmax` | TBD | `simulation.py` | TBD | 最大积分时间 |
| `n_traj` | TBD | `catalog.py` / runner | TBD | 轨迹数 |



## 11. 输出文件规范
-----------

### 单次运行结果

```
outputs/runs/{phase}/{geometry_id}/{config_hash}/result.json
```

### 汇总表

```
outputs/summaries/{phase}/summary.parquet
outputs/summaries/{phase}/summary.csv
```

### 日志

```
outputs/logs/{phase}/{task_id}.log
```

### 代表轨迹

```
outputs/runs/{phase}/{geometry_id}/{config_hash}/sample_trajectories.npz
```

## 12. agent 首轮任务清单

### Task 1

创建以下文件：

*   `src/configs/schema.py`
*   `src/adapters/legacy_simcore_adapter.py`
*   `src/adapters/catalog_bridge.py`

### Task 2

创建以下文档：

*   `docs/legacy_parameter_map.md`
*   `docs/legacy_output_map.md`

### Task 3

创建以下测试：

*   `tests/test_adapter_schema.py`
*   `tests/test_legacy_regression.py`

### Task 4

输出以下报告：

*   legacy 单次运行入口在哪里
*   legacy 参数表
*   legacy 输出字典结构
*   哪些地方最适合后续重构

