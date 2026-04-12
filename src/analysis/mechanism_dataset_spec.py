from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SCHEMA_VERSION = "mechanism_dataset_v1"

CanonicalOperatingPointLabel = Literal[
    "OP_SUCCESS_TIP",
    "OP_EFFICIENCY_TIP",
    "OP_SPEED_TIP",
    "OP_BALANCED_RIDGE_MID",
    "OP_STALE_CONTROL_OFF_RIDGE",
]

EventType = Literal[
    "bulk_motion",
    "wall_sliding",
    "gate_approach",
    "gate_capture",
    "gate_crossing",
    "trap_episode",
    "trap_escape",
]

LagReference = Literal["navigation_field", "steering_direction"]
FieldTier = Literal["required", "optional"]
FieldScope = Literal["trajectory", "event", "gate_conditioned", "shared"]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    dtype: str
    tier: FieldTier
    scope: FieldScope
    description: str
    essential_for_rate_model: bool = False
    source_hint: str | None = None


@dataclass(frozen=True)
class TableSpec:
    name: str
    description: str
    primary_key: tuple[str, ...]
    required_fields: tuple[FieldSpec, ...]
    optional_fields: tuple[FieldSpec, ...]


SHARED_REQUIRED_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="schema_version",
        dtype="string",
        tier="required",
        scope="shared",
        description="Mechanism-dataset schema identifier.",
    ),
    FieldSpec(
        name="scan_id",
        dtype="string",
        tier="required",
        scope="shared",
        description="Upstream workflow scan identifier, expected to be confirmatory_scan by default.",
    ),
    FieldSpec(
        name="state_point_id",
        dtype="string",
        tier="required",
        scope="shared",
        description="Workflow state-point hash carried through from the persisted summary/result bundle.",
        essential_for_rate_model=True,
        source_hint="outputs/summaries/*/summary.parquet",
    ),
    FieldSpec(
        name="canonical_label",
        dtype="string",
        tier="required",
        scope="shared",
        description="Frozen canonical operating-point label used as the default mechanism-analysis key.",
        essential_for_rate_model=True,
        source_hint="outputs/tables/canonical_operating_points.csv",
    ),
    FieldSpec(
        name="geometry_id",
        dtype="string",
        tier="required",
        scope="shared",
        description="Geometry identifier from the workflow summary.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="model_variant",
        dtype="string",
        tier="required",
        scope="shared",
        description="Workflow model variant such as full or no_memory.",
    ),
    FieldSpec(
        name="flow_condition",
        dtype="string",
        tier="required",
        scope="shared",
        description="Normalized flow-condition label carried from the workflow.",
    ),
    FieldSpec(
        name="analysis_source",
        dtype="string",
        tier="required",
        scope="shared",
        description="Whether the source row is base_4096 or resampled_8192.",
    ),
    FieldSpec(
        name="analysis_n_traj",
        dtype="int64",
        tier="required",
        scope="shared",
        description="Trajectory count used for the selected canonical point.",
    ),
    FieldSpec(
        name="Pi_m",
        dtype="float64",
        tier="required",
        scope="shared",
        description="Memory-to-gate dimensionless ratio.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="Pi_f",
        dtype="float64",
        tier="required",
        scope="shared",
        description="Delay-to-gate dimensionless ratio.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="Pi_U",
        dtype="float64",
        tier="required",
        scope="shared",
        description="Flow-to-swim dimensionless ratio.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="tau_g",
        dtype="float64",
        tier="required",
        scope="shared",
        description="Reference gate-crossing time used for nondimensionalization.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="l_g",
        dtype="float64",
        tier="required",
        scope="shared",
        description="Reference gate-search length used for nondimensionalization.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="result_json",
        dtype="string",
        tier="required",
        scope="shared",
        description="Path to the upstream normalized result bundle for provenance.",
        source_hint="outputs/runs/*/result.json",
    ),
)


TRAJECTORY_REQUIRED_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="traj_id",
        dtype="int64",
        tier="required",
        scope="trajectory",
        description="Trajectory identifier within a canonical operating point.",
        essential_for_rate_model=True,
        source_hint="legacy trajectory summary",
    ),
    FieldSpec(
        name="success_flag",
        dtype="bool",
        tier="required",
        scope="trajectory",
        description="Whether the trajectory reaches the exit gate successfully.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="t_stop",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Stopping time for the trajectory, equal to exit time or Tmax.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="t_exit_or_nan",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Exit time when successful, NaN otherwise.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="boundary_contact_fraction_i",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Fraction of live steps spent in boundary contact.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_gate_approach_events",
        dtype="int64",
        tier="required",
        scope="trajectory",
        description="Count of gate-approach events for the trajectory.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_gate_capture_events",
        dtype="int64",
        tier="required",
        scope="trajectory",
        description="Count of gate-capture events for the trajectory.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_gate_crossing_events",
        dtype="int64",
        tier="required",
        scope="trajectory",
        description="Count of gate-crossing events for the trajectory.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_trap_events",
        dtype="int64",
        tier="required",
        scope="trajectory",
        description="Count of trap episodes for the trajectory.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="trap_time_total",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Total time spent in trap episodes over the trajectory.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="bulk_time_total",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Total time classified as bulk motion.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="wall_sliding_time_total",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Total time classified as wall sliding.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="progress_along_navigation_total",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Integrated signed progress along the local navigation field.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="progress_along_navigation_rate",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Time-normalized progress along the local navigation field.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="phase_lag_navigation_mean",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Circular mean lag between motion heading and negative navigation gradient.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="phase_lag_steering_mean",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Circular mean lag between motion heading and controller steering direction.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="alignment_gate_mean",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Mean directional alignment measured only during gate approach, capture, and crossing contexts.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="alignment_wall_mean",
        dtype="float64",
        tier="required",
        scope="trajectory",
        description="Mean tangential alignment measured only during wall-sliding contexts.",
        essential_for_rate_model=True,
    ),
)


TRAJECTORY_OPTIONAL_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="Sigma_drag_i",
        dtype="float64",
        tier="optional",
        scope="trajectory",
        description="Per-trajectory drag-dissipation proxy already available in the legacy wrapper output.",
    ),
    FieldSpec(
        name="live_steps",
        dtype="int64",
        tier="optional",
        scope="trajectory",
        description="Number of simulated live steps used for normalization checks.",
    ),
    FieldSpec(
        name="boundary_steps",
        dtype="int64",
        tier="optional",
        scope="trajectory",
        description="Number of steps in boundary contact.",
    ),
    FieldSpec(
        name="largest_trap_duration",
        dtype="float64",
        tier="optional",
        scope="trajectory",
        description="Longest single trap episode observed in the trajectory.",
    ),
    FieldSpec(
        name="gate_visit_sequence",
        dtype="string",
        tier="optional",
        scope="trajectory",
        description="Compact serialized gate-visit sequence for debugging or visual inspection.",
    ),
)


EVENT_REQUIRED_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="event_id",
        dtype="string",
        tier="required",
        scope="event",
        description="Stable unique event identifier.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="traj_id",
        dtype="int64",
        tier="required",
        scope="event",
        description="Trajectory identifier to which the event belongs.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="event_type",
        dtype="string",
        tier="required",
        scope="event",
        description="One of the controlled mechanism-event labels.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="event_index",
        dtype="int64",
        tier="required",
        scope="event",
        description="Monotone event index within each trajectory.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="t_start",
        dtype="float64",
        tier="required",
        scope="event",
        description="Start time of the event.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="t_end",
        dtype="float64",
        tier="required",
        scope="event",
        description="End time of the event.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="duration",
        dtype="float64",
        tier="required",
        scope="event",
        description="Event duration equal to t_end - t_start.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="gate_id",
        dtype="int64",
        tier="required",
        scope="event",
        description="Gate identifier if the event is gate-conditioned, otherwise -1.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="entered_from_event_type",
        dtype="string",
        tier="required",
        scope="event",
        description="Previous event type before this event started.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="exited_to_event_type",
        dtype="string",
        tier="required",
        scope="event",
        description="Next event type after this event ended.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="progress_along_navigation",
        dtype="float64",
        tier="required",
        scope="event",
        description="Integrated signed progress along the navigation field over the event.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="progress_along_navigation_rate",
        dtype="float64",
        tier="required",
        scope="event",
        description="Progress along navigation divided by duration.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="phase_lag_navigation_mean",
        dtype="float64",
        tier="required",
        scope="event",
        description="Circular mean lag between motion heading and navigation direction during the event.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="phase_lag_steering_mean",
        dtype="float64",
        tier="required",
        scope="event",
        description="Circular mean lag between motion heading and steering direction during the event.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="alignment_gate_mean",
        dtype="float64",
        tier="required",
        scope="event",
        description="Mean gate-axis alignment over the event, required for gate approach/capture/crossing.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="alignment_wall_mean",
        dtype="float64",
        tier="required",
        scope="event",
        description="Mean tangential wall alignment over the event, required for wall-sliding and trap events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="capture_success_flag",
        dtype="bool",
        tier="required",
        scope="event",
        description="Whether a gate-capture event proceeds to crossing rather than returning to wall or bulk.",
        essential_for_rate_model=True,
    ),
)


EVENT_OPTIONAL_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="x_start",
        dtype="float64",
        tier="optional",
        scope="event",
        description="Start x-position for visualization and debugging.",
    ),
    FieldSpec(
        name="y_start",
        dtype="float64",
        tier="optional",
        scope="event",
        description="Start y-position for visualization and debugging.",
    ),
    FieldSpec(
        name="x_end",
        dtype="float64",
        tier="optional",
        scope="event",
        description="End x-position for visualization and debugging.",
    ),
    FieldSpec(
        name="y_end",
        dtype="float64",
        tier="optional",
        scope="event",
        description="End y-position for visualization and debugging.",
    ),
    FieldSpec(
        name="mean_wall_distance",
        dtype="float64",
        tier="optional",
        scope="event",
        description="Average signed wall distance over the event.",
    ),
    FieldSpec(
        name="mean_gate_distance",
        dtype="float64",
        tier="optional",
        scope="event",
        description="Average distance to the active gate over the event.",
    ),
    FieldSpec(
        name="mean_speed",
        dtype="float64",
        tier="optional",
        scope="event",
        description="Average speed over the event.",
    ),
)


GATE_REQUIRED_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="gate_id",
        dtype="int64",
        tier="required",
        scope="gate_conditioned",
        description="Gate identifier for the conditioned summary.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_gate_approach",
        dtype="int64",
        tier="required",
        scope="gate_conditioned",
        description="Number of gate-approach events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_gate_capture",
        dtype="int64",
        tier="required",
        scope="gate_conditioned",
        description="Number of gate-capture events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="n_gate_crossing",
        dtype="int64",
        tier="required",
        scope="gate_conditioned",
        description="Number of gate-crossing events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="capture_given_approach",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Empirical probability of capture conditional on approach.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="crossing_given_capture",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Empirical probability of crossing conditional on capture.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="mean_approach_duration",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Mean duration of approach events at the gate.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="mean_capture_duration",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Mean duration of capture events at the gate.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="mean_crossing_duration",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Mean duration of crossing events at the gate.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="alignment_at_gate_mean",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Gate-axis alignment averaged over approach, capture, and crossing near the gate.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="phase_lag_navigation_at_gate_mean",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Navigation-field lag conditioned on gate-local events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="phase_lag_steering_at_gate_mean",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Steering-direction lag conditioned on gate-local events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="progress_rate_at_gate_mean",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Average progress-along-navigation rate during gate-local events.",
        essential_for_rate_model=True,
    ),
    FieldSpec(
        name="return_to_wall_after_capture_rate",
        dtype="float64",
        tier="required",
        scope="gate_conditioned",
        description="Fraction of capture events that fail by returning to wall-sliding or trap contexts.",
        essential_for_rate_model=True,
    ),
)


GATE_OPTIONAL_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec(
        name="gate_x",
        dtype="float64",
        tier="optional",
        scope="gate_conditioned",
        description="Gate center x-coordinate for plotting or geometry transfer.",
    ),
    FieldSpec(
        name="gate_y",
        dtype="float64",
        tier="optional",
        scope="gate_conditioned",
        description="Gate center y-coordinate for plotting or geometry transfer.",
    ),
    FieldSpec(
        name="mean_approach_angle",
        dtype="float64",
        tier="optional",
        scope="gate_conditioned",
        description="Average signed approach angle relative to the gate normal.",
    ),
    FieldSpec(
        name="mean_capture_depth",
        dtype="float64",
        tier="optional",
        scope="gate_conditioned",
        description="Mean penetration depth into the gate neighborhood before crossing or return.",
    ),
)


TRAJECTORY_TABLE_SPEC = TableSpec(
    name="mechanism_trajectory_records",
    description="One row per trajectory for the frozen canonical operating points.",
    primary_key=("canonical_label", "state_point_id", "traj_id"),
    required_fields=SHARED_REQUIRED_FIELDS + TRAJECTORY_REQUIRED_FIELDS,
    optional_fields=TRAJECTORY_OPTIONAL_FIELDS,
)

EVENT_TABLE_SPEC = TableSpec(
    name="mechanism_event_records",
    description="One row per classified event episode within a trajectory.",
    primary_key=("canonical_label", "state_point_id", "traj_id", "event_index"),
    required_fields=SHARED_REQUIRED_FIELDS + EVENT_REQUIRED_FIELDS,
    optional_fields=EVENT_OPTIONAL_FIELDS,
)

GATE_CONDITIONED_TABLE_SPEC = TableSpec(
    name="mechanism_gate_conditioned_records",
    description="One row per canonical point and gate for coarse-grained gate-theory fitting.",
    primary_key=("canonical_label", "state_point_id", "gate_id"),
    required_fields=SHARED_REQUIRED_FIELDS + GATE_REQUIRED_FIELDS,
    optional_fields=GATE_OPTIONAL_FIELDS,
)


EVENT_VOCABULARY: dict[str, str] = {
    "bulk_motion": "Motion away from walls and outside any gate-neighborhood, used as the search state in rate models.",
    "wall_sliding": "Boundary-contact motion with strong tangential alignment to the wall and no gate capture yet.",
    "gate_approach": "Entry into a gate neighborhood while moving under gate-oriented progress but before geometric capture.",
    "gate_capture": "Residence inside the gate-neighborhood basin where the trajectory is committed to a specific gate but has not yet crossed.",
    "gate_crossing": "Successful transit across the gate surface or threshold.",
    "trap_episode": "Extended low-progress residence near a wall or gate mouth with repeated ineffective motion.",
    "trap_escape": "Transition out of a trap episode back into bulk, wall sliding, or gate-approach motion.",
}


MEASUREMENT_NOTES: dict[str, str] = {
    "phase_lag_navigation": (
        "Signed angular lag between the instantaneous motion heading and the local navigation direction "
        "d_nav = -grad(psi) / ||grad(psi)||, aggregated with circular means."
    ),
    "phase_lag_steering": (
        "Signed angular lag between the instantaneous motion heading and the controller steering direction "
        "actually supplied to the delayed feedback law; if the controller uses a delayed navigation vector, "
        "this is measured relative to that delayed vector rather than the instantaneous field."
    ),
    "alignment_at_gate": (
        "Cosine alignment between motion heading and the gate-forward direction, evaluated only inside gate approach, "
        "capture, and crossing contexts."
    ),
    "alignment_on_wall": (
        "Tangential wall alignment defined as the cosine between motion heading and the local wall tangent; "
        "the normal component may be recorded optionally for debugging but is not required."
    ),
    "progress_along_navigation": (
        "Signed scalar progress rate v · d_nav, where v is instantaneous velocity and d_nav is the normalized "
        "navigation direction. Event and trajectory totals are time integrals of this quantity."
    ),
}


COARSE_GRAINED_GATE_THEORY_ESSENTIALS: tuple[str, ...] = (
    "n_gate_approach",
    "n_gate_capture",
    "n_gate_crossing",
    "capture_given_approach",
    "crossing_given_capture",
    "mean_approach_duration",
    "mean_capture_duration",
    "mean_crossing_duration",
    "return_to_wall_after_capture_rate",
    "phase_lag_navigation_at_gate_mean",
    "phase_lag_steering_at_gate_mean",
    "alignment_at_gate_mean",
    "progress_rate_at_gate_mean",
    "wall_sliding_time_total",
    "trap_time_total",
)


def all_table_specs() -> tuple[TableSpec, ...]:
    return (
        TRAJECTORY_TABLE_SPEC,
        EVENT_TABLE_SPEC,
        GATE_CONDITIONED_TABLE_SPEC,
    )


def required_field_names(table_spec: TableSpec) -> tuple[str, ...]:
    return tuple(field.name for field in table_spec.required_fields)


def optional_field_names(table_spec: TableSpec) -> tuple[str, ...]:
    return tuple(field.name for field in table_spec.optional_fields)
