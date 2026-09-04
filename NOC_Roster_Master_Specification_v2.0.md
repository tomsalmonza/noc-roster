# NOC Roster Master Specification
## Version 2.0
### Master Markdown Specification

---

# Document Information

| Item | Value |
|------|-------|
| Document | NOC Roster Master Specification |
| Version | 2.0 |
| Status | Draft |
| Purpose | Master specification for generation and validation of the Network Operations Centre roster |
| Roster Period | 1 August 2026 – 31 July 2027 |
| Staff Complement | 10 Employees |
| Shift Model | 24 × 7 Continuous Operations |

---

# Revision History

| Version | Description |
|----------|-------------|
| 1.0 | Initial roster specification |
| 1.1 | Added leave assumptions, public holiday planning, RQS, FI and weekend ownership |
| 2.0 | Consolidated master specification |

---

# Table of Contents

1. Purpose
2. Design Principles
3. Terminology
4. System Overview
5. Staff Model
6. Shift Definitions
7. Daily Staffing Model
8. Group Rules
9. Standby Model
10. Fatigue Management
11. Off-Day Philosophy
12. Weekend Allocation
13. Public Holidays
14. Leave Planning
15. Employee Availability Assumptions
16. Cover Model
17. Annual Shift Accounting
18. Fairness Metrics
19. Fairness Targets
20. Shift Weight Model
21. Pairing Diversity
22. Fairness Index
23. Roster Quality Score
24. Workbook Outputs
25. Optimisation Hierarchy

---

# 1. Purpose

This specification defines every operational rule, planning assumption, fairness metric, optimisation objective and validation rule required to generate the annual Network Operations Centre roster.

This document is the authoritative source for roster generation.

All future roster implementations shall comply with this specification.

---

# 2. Design Principles

The roster shall satisfy the following objectives.

## 2.1 Operational Continuity

The NOC operates continuously.

Every operational shift shall always be staffed.

---

## 2.2 Staff Safety

Fatigue management shall be prioritised.

The roster should minimise fatigue wherever practical.

---

## 2.3 Fairness

Operational workload should be distributed as evenly as practical.

Fairness includes:

- Operational shifts
- Night shifts
- Weekend shifts
- Public holidays
- Premium public holidays
- Standby
- Pairing diversity
- Shift weight

---

## 2.4 Simplicity

The roster should be predictable.

Employees should be able to recognise repeating patterns where practical.

---

## 2.5 Maintainability

The base roster shall remain stable.

Leave and sickness should be accommodated using the standby and cover process rather than requiring regeneration of the annual roster.

---

# 3. Terminology

## Operational Shift

An Operational Shift is one of:

- Morning
- Afternoon
- Night

Only operational shifts contribute to the annual operational shift target.

---

## Paid Shift

A Paid Shift is any rostered operational assignment that contributes towards the annual paid shift allocation.

Paid shifts include:

- Morning
- Afternoon
- Night
- Approved Annual Leave
- Approved Sick Leave
- Approved Family Responsibility Leave
- Public Holiday Leave Equivalent

---

## Standby

Standby is a reserve assignment.

Standby is not an operational shift.

Standby does not count towards annual operational shift totals.

Standby only becomes operational work if the employee is activated for cover.

---

## Off

An Off assignment is a scheduled rest day.

---

## Cover Shift

A Cover Shift occurs when an employee performs operational work while originally rostered as Standby or Off.

Cover shifts are excluded from the base roster generation.

---

## Full Weekend Off

A Full Weekend Off consists of:

- Saturday Off
- Sunday Off

Standby does not qualify.

---

## Designated Weekend Owner

Each calendar week has one employee designated as the official Full Weekend Off owner.

Other employees may coincidentally receive a full weekend off.

Only the designated owner contributes to the Weekend Ownership metric.

---

## Holiday Worked Score

A cumulative measure of undesirable public holiday assignments.

Higher scores indicate a greater public holiday burden.

---

## Shift Weight Score

A weighted measure of annual operational workload.

Night shifts and premium public holidays attract higher weighting.

---

## Fairness Index (FI)

The Fairness Index measures the overall fairness of the annual roster.

Higher values indicate greater fairness.

---

## Roster Quality Score (RQS)

The Roster Quality Score measures how effectively the generated roster satisfies all soft constraints after every hard constraint has been satisfied.

---

# 4. System Overview

## Roster Duration

The roster covers:

**1 August 2026 to 31 July 2027**

Duration:

365 calendar days.

---

## Staff Complement

The roster contains:

10 permanent employees.

---

## Employee Groups

The employees are divided into two groups.

### Group A

- S1
- S2
- S3
- S4
- S5

### Group B

- S6
- S7
- S8
- S9
- S10

These groups are used to enforce operational pairing rules.

---

# 5. Staff Model

Every employee shall receive one assignment every calendar day.

Valid assignments are:

- Morning
- Afternoon
- Night
- Standby
- Off

No employee may receive more than one assignment on the same calendar day.

---

# 6. Shift Definitions

| Shift | Abbreviation | Time |
|--------|--------------|------|
| Morning | M | 06:00–14:00 |
| Afternoon | A | 14:00–22:00 |
| Night | N | 22:00–06:00 |
| Standby | SB | On Call |
| Off | OFF | Rest Day |

Morning, Afternoon and Night are operational shifts.

Standby and Off are non-operational assignments.

---

# 7. Daily Staffing Model

Every calendar day shall contain exactly:

| Assignment | Employees |
|------------|----------:|
| Morning | 2 |
| Afternoon | 2 |
| Night | 2 |
| Standby | 2 |
| Off | 2 |

Total daily staff:

10

No deviations are permitted.

---

# 8. Group Rules

Each operational shift shall contain:

- One Group A employee
- One Group B employee

This applies to:

- Morning
- Afternoon
- Night

The following combinations are prohibited:

- Group A + Group A
- Group B + Group B

Standby assignments are not required to follow this pairing rule.

Off assignments are not required to follow this pairing rule.

---

# 9. Standby Model

Each calendar day shall contain:

- One Group A employee on Standby
- One Group B employee on Standby

Standby assignments are intended to provide operational resilience.

Standby employees may be activated to provide operational cover.

If activated:

- the employee performs a Cover Shift;
- the Cover Shift is recorded separately from the base roster; and
- the Cover Shift contributes to payroll and reporting.

Standby assignments do not contribute towards the annual operational shift target unless activated.

---

# 10. Fatigue Management

The fatigue management rules are intended to reduce excessive workload, improve employee wellbeing and maintain operational safety.

Fatigue management consists of both hard constraints and soft optimisation objectives.

---

## 10.1 Maximum Consecutive Night Shifts

No employee may be assigned more than:

**3 consecutive Night shifts**

The following pattern is permitted:

```
N N N OFF
```

The following pattern is prohibited:

```
N N N N
```

This is a hard constraint.

---

## 10.2 Night to Morning Restriction

The following transition is prohibited:

```
Night → Morning
```

on consecutive calendar days.

Example:

| Day | Assignment |
|-----|------------|
| Monday | Night |
| Tuesday | Morning |

This roster is invalid.

This is a hard constraint.

---

## 10.3 Preferred Night Recovery

Following two or three consecutive Night shifts, the preferred recovery sequence is:

```
Night Block → Standby
```

or

```
Night Block → Off
```

This improves fatigue recovery and contributes positively to roster quality.

This is a soft optimisation objective.

---

## 10.4 Standby to Morning Recovery

The following transition should be avoided where operationally practical:

```
Standby → Morning
```

Reason:

A Standby employee may have been activated during the standby period to perform operational work. Assigning Morning duty immediately afterwards increases fatigue risk.

This is a soft optimisation objective.

RQS Penalty:

```
-2
```

---

## 10.5 Consecutive Working Days

The preferred maximum work block is:

```
6 consecutive worked days
```

Where possible, the roster should insert either:

- Off
- Standby

before a seventh consecutive worked day.

This is a soft optimisation objective.

---

# 11. Off-Day Philosophy

The roster should approximately follow a:

```
5 Days On
2 Days Off
```

pattern where operationally practical.

This is not a hard constraint.

The optimiser may deviate where required to satisfy higher-priority constraints.

---

## 11.1 Consecutive Off Days

The preferred recovery sequence is:

```
OFF
OFF
```

rather than isolated Off days.

Three consecutive Off days are permitted where required.

---

## 11.2 Isolated Off Day

An isolated Off day exists when the following pattern occurs:

```
Work → OFF → Work
```

where:

Work is one of:

- Morning
- Afternoon
- Night

Standby is not considered a worked shift.

The following patterns shall **not** be treated as isolated Off days:

```
Work → OFF → Standby
```

```
Standby → OFF → Work
```

```
Night Block → OFF → Work
```

Only true isolated Off days attract an RQS penalty.

Penalty:

```
-1
```

---

# 12. Weekend Allocation

Weekend allocation is intended to distribute desirable weekends fairly while maintaining operational staffing.

---

## 12.1 Full Weekend Off

A Full Weekend Off consists of:

- Saturday Off
- Sunday Off

Standby does not qualify.

---

## 12.2 Weekend Ownership

Each calendar week shall have exactly one designated Weekend Owner.

The designated Weekend Owner receives the official Full Weekend Off allocation for that week.

Other employees may coincidentally receive a full weekend off through normal roster rotation.

Only the designated Weekend Owner contributes to the Weekend Ownership metric.

---

## 12.3 Weekend Rotation

The designated Weekend Owner rotates as follows:

| Week | Employee |
|------|----------|
| 1 | S1 |
| 2 | S2 |
| 3 | S3 |
| 4 | S4 |
| 5 | S5 |
| 6 | S6 |
| 7 | S7 |
| 8 | S8 |
| 9 | S9 |
| 10 | S10 |

The cycle then repeats.

---

## 12.4 Ten-Week Rule

Within any ten-week rotation cycle:

No employee may be assigned more than one designated Full Weekend Off.

This is a hard constraint.

---

## 12.5 Preferred Weekend Pattern

Preferred sequence:

```
Friday OFF or Standby
Saturday OFF
Sunday OFF
```

Acceptable:

```
Friday Afternoon
Saturday OFF
Sunday OFF
```

Least preferred:

```
Friday Night
Saturday OFF
Sunday OFF
```

Friday Night before a designated Full Weekend Off attracts an RQS penalty.

Penalty:

```
-1
```

---

## 12.6 Monday Return

Employees may return to duty on Monday Morning following a designated Full Weekend Off.

No recovery day is required.

---

## 12.7 Weekend Shift Fairness

Weekend operational shifts shall be distributed as evenly as possible.

Target variance:

```
±1 weekend shift
```

from the team average.

This is a soft optimisation objective.

## 12.8 Actual Full Weekend Off Fairness

Actual Full Weekends Off shall be distributed as evenly as possible across all
employees. The optimiser shall minimise variance in each employee's count of
Saturday and Sunday both assigned as Off, while preserving as many Full
Weekends Off as practical.

Target:

```
Minimum practical variance; equal counts where feasible.
```

This is a soft optimisation objective.

---

# 13. Public Holidays

The roster shall include the following South African public holidays falling within the roster period.

## 2026

- National Women's Day (Observed) – 10 August
- Heritage Day – 24 September
- Day of Reconciliation – 16 December
- Christmas Day – 25 December
- Day of Goodwill – 26 December

---

## 2027

- New Year's Day – 1 January
- Human Rights Day (Observed) – 22 March
- Good Friday – 26 March
- Family Day – 29 March
- Freedom Day – 27 April
- Workers' Day – 1 May
- Youth Day – 16 June

---

## 13.1 Holiday Worked Score

Each employee maintains a cumulative Holiday Worked Score.

| Holiday | Score |
|---------|------:|
| Standard Public Holiday | 1.0 |
| Day of Goodwill | 1.5 |
| Christmas Day | 2.0 |
| New Year's Day | 2.0 |

Only Morning, Afternoon and Night assignments contribute.

Standby and Off do not contribute.

---

## 13.2 Holiday Allocation

When assigning public holiday operational shifts, preference should be given to employees with the lowest cumulative Holiday Worked Score.

Objective:

Minimise Holiday Worked Score variance across all employees.

This is a soft optimisation objective.

---

## 13.3 Premium Holidays

Premium Holidays are defined as:

- Christmas Day
- Day of Goodwill
- New Year's Day

---

## 13.4 Premium Holiday Preferences

Where operationally practical:

- Employees working Christmas Day should preferably not work New Year's Day.
- Employees working Christmas Night should preferably not work New Year's Night.
- Employees working Christmas Day should preferably not work Day of Goodwill.
- No employee should receive more than two Premium Holiday operational assignments during the festive season.

These are soft optimisation objectives.

---

# 14. Leave Planning

The annual base roster shall be generated before leave is allocated.

Leave planning is a secondary scheduling activity.

The base roster shall remain unchanged wherever practical.

---

## 14.1 Leave Planning Window

Annual leave should preferably be planned at least:

```
90 days
```

before commencement.

---

## 14.2 Leave Replacement

When an employee is absent:

Operational cover shall be provided using the Cover Model defined later in this specification.

The base roster itself should not be regenerated.

---

# 15. Employee Availability Assumptions

This section defines the workforce planning assumptions used when calculating annual staffing capacity, paid shift targets and fairness metrics.

These assumptions are used for:

- Annual roster generation
- Workforce planning
- Capacity planning
- Fairness calculations
- Annual reporting

---

## 15.1 Annual Planning Assumptions

| Category | Days |
|----------|-----:|
| Paid Shift Target | 260 |
| Annual Leave | 21 |
| Public Holiday Leave Equivalent | 10 |
| Sick / Family Responsibility Leave | 10 |
| Expected Operational Shifts Worked | 219 |

---

## 15.2 Operational Shift Target

The roster contains:

- 6 operational positions per day
- 365 calendar days

Total operational assignments:

```
365 × 6 = 2,190
```

Average operational assignments:

```
2,190 ÷ 10 = 219
```

Therefore every employee shall be allocated:

```
219 operational shifts
```

during the roster period.

This is a hard constraint.

---

## 15.3 Paid Shift Definition

Paid shifts consist of:

- Morning
- Afternoon
- Night
- Annual Leave occurring on a rostered operational shift
- Public Holiday Leave Equivalent occurring on a rostered operational shift
- Sick Leave occurring on a rostered operational shift
- Family Responsibility Leave occurring on a rostered operational shift

Standby assignments are not paid shifts unless activated.

Off assignments are not paid shifts.

---

## 15.4 Leave Planning Assumption

For annual planning purposes every employee is assumed to utilise:

| Leave Category | Days |
|---------------|-----:|
| Annual Leave | 21 |
| Public Holiday Leave Equivalent | 10 |
| Sick / Family Responsibility Leave | 10 |
| Total Leave / Absence | 41 |

Therefore:

```
260 Paid Shifts
−41 Leave Equivalents
--------------------
219 Operational Shifts
```

---

## 15.5 Planning Principle

These assumptions are planning metrics.

Actual leave dates are allocated after the annual roster has been generated.

---

# 16. Cover Model

The cover process operates independently of the base roster.

Cover assignments are created only when a rostered employee becomes unavailable.

Examples include:

- Annual Leave
- Sick Leave
- Family Responsibility Leave
- Training
- Compassionate Leave
- Other approved absences

---

## 16.1 Cover Priority

Operational cover shall be allocated in the following order.

Priority 1

```
Standby Employee (same group if practical)
```

Priority 2

```
Other Standby Employee
```

Priority 3

```
Off Employee
```

Priority 4

```
Manual Operational Decision
```

---

## 16.2 Cover Accounting

Cover shifts shall be recorded separately from the base roster.

Cover shifts:

- contribute to payroll;
- contribute to overtime where applicable;
- do not alter the annual base roster statistics.

---

# 17. Annual Shift Accounting

---

## 17.1 Operational Assignments

Daily operational assignments:

| Shift | Employees |
|--------|----------:|
| Morning | 2 |
| Afternoon | 2 |
| Night | 2 |

Daily total:

```
6
```

Annual total:

```
365 × 6 = 2,190
```

---

## 17.2 Employee Operational Target

Each employee shall receive:

```
219 operational assignments
```

during the roster year.

This is a hard constraint.

---

## 17.3 Paid Shift Target

Each employee has an annual paid shift target of:

```
260
```

comprised of:

- Operational shifts worked
- Leave equivalents

---

## 17.4 Standby Accounting

Standby assignments:

- are recorded separately;
- do not contribute towards operational shift totals;
- do not contribute towards paid shift totals unless activated.

---

## 17.5 Off Accounting

Off assignments:

- are recorded separately;
- contribute towards fatigue management;
- do not contribute towards operational shift totals.

---

# 18. Fairness Metrics

The following annual statistics shall be maintained for every employee.

---

## 18.1 Shift Counts

- Morning
- Afternoon
- Night

---

## 18.2 Weekend Statistics

- Weekend operational shifts
- Designated Full Weekends Off
- Actual Full Weekends Off

---

## 18.3 Standby Statistics

- Total Standby assignments

---

## 18.4 Off Statistics

- Total Off assignments

---

## 18.5 Holiday Statistics

- Public Holidays Worked
- Premium Holidays Worked
- Holiday Worked Score

---

## 18.6 Shift Weight Statistics

Annual Shift Weight Score.

---

## 18.7 Pairing Statistics

Pairing frequency with every opposite-group employee.

---

## 18.8 Quality Statistics

- RQS Penalty
- FI Contribution

---

# 19. Fairness Targets

The objective is to ensure that no employee is systematically disadvantaged.

---

## 19.1 Operational Shift Target

Each employee:

```
219 operational shifts
```

Hard constraint.

---

## 19.2 Morning Shift Target

Preferred range:

```
71–75
```

Soft optimisation objective.

---

## 19.3 Afternoon Shift Target

Preferred range:

```
71–75
```

Soft optimisation objective.

---

## 19.4 Night Shift Target

Preferred range:

```
71–75
```

Soft optimisation objective.

---

## 19.5 Weekend Shift Target

Weekend operational shifts should remain within:

```
±1
```

of the team average.

Soft optimisation objective.

---

## 19.6 Standby Distribution

Standby assignments should be distributed as evenly as practical.

Soft optimisation objective.

---

## 19.7 Off Distribution

Off assignments should be distributed as evenly as practical.

Soft optimisation objective.

---

## 19.8 Holiday Worked Score

Holiday Worked Scores should remain as equal as practical.

Soft optimisation objective.

---

## 19.9 Premium Holiday Allocation

Premium Holiday assignments should be distributed as evenly as practical.

Soft optimisation objective.

---

## 19.10 Shift Weight Score

Shift Weight Scores should remain within:

```
±5%
```

of the team average where practical.

Soft optimisation objective.

---

## 19.11 Pairing Diversity

Pairing frequencies should remain balanced across all possible Group A / Group B combinations.

Soft optimisation objective.

---

# 20. Shift Weight Model

The Shift Weight Model measures the relative workload carried by each employee over the roster period.

Not all operational shifts are considered equal. Night shifts and Premium Public Holiday shifts impose a greater operational burden and therefore carry a higher weighting.

The objective is to minimise the variance in Shift Weight Score across all employees.

---

## 20.1 Standard Shift Weighting

| Assignment | Weight |
|------------|-------:|
| Morning | 1.0 |
| Afternoon | 1.0 |
| Night | 1.2 |
| Standby | 0.0 |
| Off | 0.0 |

---

## 20.2 Public Holiday Weighting

| Assignment | Weight |
|------------|-------:|
| Public Holiday Morning | 1.3 |
| Public Holiday Afternoon | 1.3 |
| Public Holiday Night | 1.5 |
| Christmas Day Morning | 1.8 |
| Christmas Day Afternoon | 1.8 |
| Christmas Day Night | 2.0 |
| New Year's Day Morning | 1.8 |
| New Year's Day Afternoon | 1.8 |
| New Year's Day Night | 2.0 |

---

## 20.3 Consecutive Night Weighting

Additional fatigue weighting shall apply to consecutive Night shifts.

| Consecutive Night | Weight |
|------------------|-------:|
| First | 1.2 |
| Second | 1.3 |
| Third | 1.4 |

---

## 20.4 Shift Weight Target

The annual Shift Weight Score should remain within:

```
±5%
```

of the team average where operationally practical.

This is a soft optimisation objective.

---

# 21. Pairing Diversity

Operational shifts are staffed by one employee from Group A and one employee from Group B.

Pairing diversity encourages knowledge sharing, cross-training and balanced team cohesion.

---

## 21.1 Objective

Repeated pairings should be minimised.

Every Group A employee should work with every Group B employee as evenly as practical.

---

## 21.2 Pairing Matrix

Pairing frequency shall be maintained for every possible pairing.

Example:

| Group A | Group B | Count |
|----------|----------|------:|
| S1 | S6 | X |
| S1 | S7 | X |
| S1 | S8 | X |
| S1 | S9 | X |
| S1 | S10 | X |

This applies equally to every employee.

---

## 21.3 Pairing Target

Pairing frequencies should remain within approximately:

```
±10%
```

of the average pairing count.

This is a soft optimisation objective.

---

# 22. Fairness Index (FI)

The Fairness Index measures the overall fairness of the annual roster.

The FI is intended to provide a single numerical indication of how evenly workload has been distributed.

Higher values indicate greater fairness.

---

## 22.1 Components

The Fairness Index considers:

- Operational Shift Count
- Morning Shift Distribution
- Afternoon Shift Distribution
- Night Shift Distribution
- Weekend Shift Distribution
- Standby Distribution
- Off Distribution
- Holiday Worked Score
- Premium Holiday Allocation
- Shift Weight Score
- Pairing Diversity
- Designated Weekend Ownership

---

## 22.2 Rating Scale

| Score | Rating |
|--------|---------|
| 95–100 | Excellent |
| 90–94 | Very Good |
| 80–89 | Good |
| 70–79 | Acceptable |
| Below 70 | Review Required |

---

## 22.3 Objective

The optimisation process should maximise the Fairness Index after all hard constraints have been satisfied.

---

# 23. Roster Quality Score (RQS)

The Roster Quality Score measures how effectively the roster satisfies all soft constraints.

The RQS is calculated only after every hard constraint has been satisfied.

A roster violating any hard constraint is invalid regardless of its RQS.

---

## 23.1 Starting Score

Every roster begins with:

```
100
```

Penalty points are deducted for soft constraint violations.

The objective is to maximise the final score.

---

## 23.2 Fatigue Penalties

### Standby followed by Morning

Pattern:

```
Standby → Morning
```

Penalty:

```
-2
```

---

### Night Block followed by Afternoon

Pattern:

```
Night Block → Afternoon
```

Penalty:

```
-1
```

---

### Night followed by Morning

Pattern:

```
Night → Morning
```

Result:

```
Invalid Roster
```

This is a hard constraint and is not scored.

---

## 23.3 Weekend Quality Penalty

Pattern:

```
Friday Night
Saturday OFF
Sunday OFF
```

Penalty:

```
-1
```

---

## 23.4 Consecutive Working Days

| Pattern | Penalty |
|----------|--------:|
| 7 consecutive worked days | -2 |
| 8 consecutive worked days | -4 |
| More than 8 consecutive worked days | -10 |

Worked days consist of:

- Morning
- Afternoon
- Night

Standby and Off are not considered worked days for this rule.

---

## 23.5 Off-Day Quality

Only true isolated Off days are penalised.

Penalty:

```
Work → OFF → Work
```

```
-1
```

The following patterns do not attract a penalty:

```
Work → OFF → Standby
```

```
Standby → OFF → Work
```

```
Night Block → OFF → Work
```

---

## 23.6 Standby Distribution

At year end:

Standby assignments exceeding approximately 10% above the team average attract:

```
-1
```

per additional assignment.

---

## 23.7 Night Shift Distribution

Night shift allocations exceeding approximately 5% above the team average attract:

```
-1
```

per additional Night shift.

---

## 23.8 Weekend Shift Distribution

Weekend operational shifts exceeding:

```
Team Average +1
```

attract:

```
-1
```

per additional Weekend shift.

---

## 23.9 Holiday Worked Score

Holiday Worked Scores above the team average attract:

```
-1
```

per score point above the average.

---

## 23.10 Shift Weight Score

Shift Weight Scores exceeding the team average by more than:

```
2%
```

attract:

```
-1
```

for every additional 2%.

---

## 23.11 Pairing Diversity

Repeated pairings above the expected average attract:

```
-0.5
```

per occurrence.

---

## 23.12 Premium Holiday Allocation

Premium Holiday assignments above the team average attract:

```
-2
```

per additional Premium Holiday assignment.

---

## 23.13 RQS Rating Scale

| Score | Rating |
|--------|---------|
| 95–100 | Excellent |
| 90–94 | Very Good |
| 80–89 | Good |
| 70–79 | Acceptable |
| 60–69 | Poor |
| Below 60 | Rebuild Recommended |

---

## 23.14 Optimisation Objective

The optimisation process should maximise RQS while preserving all hard constraints.

---

## 23.15 Tie-Breaking

Where multiple valid rosters exist with equal hard constraint compliance, preference shall be given in the following order:

1. Highest RQS
2. Highest Fairness Index
3. Lowest Holiday Worked Score variance
4. Lowest Shift Weight Score variance
5. Lowest Weekend Shift variance
6. Highest Pairing Diversity

---

# 24. Workbook Outputs

The annual roster generation process shall produce a single workbook containing all data required for operational use, planning, validation and auditing.

The workbook shall contain the following worksheets.

---

# 24.1 Specification Notes

Purpose:

Provide the governing assumptions used to generate the roster.

Contents:

- Specification version
- Generation date
- Solver configuration
- Planning assumptions
- Hard constraint summary
- Soft constraint summary
- Optimisation priorities
- Known assumptions
- Change history

---

# 24.2 Daily Roster

Purpose:

Provide the complete operational roster for the roster period.

Rows:

- One row per calendar day

Columns:

- Date
- Day of Week
- Morning Pair
- Afternoon Pair
- Night Pair
- Standby Employees
- Off Employees
- Notes

Requirements:

- Every employee shall have exactly one assignment per day.
- Operational shifts shall satisfy all pairing constraints.
- Dates shall be continuous with no omissions.

---

# 24.3 Employee Summary

Purpose:

Provide an annual summary for each employee.

Required fields:

- Employee
- Group
- Morning Shifts
- Afternoon Shifts
- Night Shifts
- Operational Shifts
- Standby Assignments
- Off Assignments
- Paid Shift Target
- Leave Equivalents
- Weekend Operational Shifts
- Designated Full Weekends Off
- Actual Full Weekends Off
- Public Holidays Worked
- Premium Holidays Worked
- Holiday Worked Score
- Shift Weight Score
- Pairing Diversity Score
- RQS Penalty Total

---

# 24.4 Public Holiday Report

Purpose:

Summarise operational staffing across all public holidays.

Required fields:

- Holiday
- Date
- Morning Staff
- Afternoon Staff
- Night Staff
- Standby Staff
- Off Staff

Summary statistics:

- Holiday Worked Score by employee
- Premium Holiday allocations
- Holiday fairness variance

---

# 24.5 Weekend Report

Purpose:

Summarise weekend allocations.

Required fields:

- Week Number
- Weekend Owner
- Saturday Assignments
- Sunday Assignments
- Designated Full Weekend Off
- Actual Full Weekends Off

Summary statistics:

- Weekend operational shifts
- Weekend ownership distribution
- Weekend variance

---

# 24.6 Pairing Analysis

Purpose:

Measure operational pairing diversity.

Required outputs:

Pairing matrix showing every:

Group A

paired with every

Group B

Required statistics:

- Pair count
- Average pair count
- Minimum
- Maximum
- Variance

---

# 24.7 Fairness Dashboard

Purpose:

Provide a high-level overview of roster quality.

Metrics:

- Fairness Index
- Roster Quality Score
- Operational Shift Variance
- Morning Shift Variance
- Afternoon Shift Variance
- Night Shift Variance
- Weekend Shift Variance
- Standby Variance
- Holiday Worked Score Variance
- Shift Weight Score Variance
- Pairing Diversity Variance

Recommended charts:

- Shift distribution
- Weekend distribution
- Holiday distribution
- Shift weight distribution
- Pairing heat map

---

# 24.8 Leave Planner

Purpose:

Support annual leave planning after the base roster has been generated.

Suggested fields:

- Employee
- Quarter
- Requested Leave
- Approved Leave
- Leave Balance
- Cover Employee
- Cover Status

The Leave Planner shall not modify the base roster.

---

# 24.9 Constraint Violations

Purpose:

Provide a complete audit of every validation performed.

The worksheet shall distinguish between:

Hard Constraint Violations

and

Soft Constraint Penalties.

Required fields:

- Rule
- Date
- Employee
- Description
- Severity
- Penalty
- Resolution

---

# 24.10 Optional Worksheets

The following worksheets may be generated where additional analysis is required.

### Shift Calendar

Monthly calendar view of assignments.

### Cover Log

Operational cover history.

### Leave Statistics

Leave utilisation summary.

### Solver Statistics

Optimisation statistics including:

- Solve time
- Iterations
- Objective value
- Hard constraint count
- Soft constraint count

---

# 25. Validation Rules

Every generated roster shall be validated before acceptance.

Validation consists of:

- Hard Constraint Validation
- Soft Constraint Evaluation
- Fairness Assessment
- Quality Assessment

---

## 25.1 Hard Constraint Validation

The following checks shall always pass.

### Daily Assignment

Every employee shall have exactly one assignment per calendar day.

---

### Daily Staffing

Every day shall contain exactly:

- 2 Morning
- 2 Afternoon
- 2 Night
- 2 Standby
- 2 Off

---

### Group Pairing

Every operational shift shall contain:

- 1 Group A employee
- 1 Group B employee

---

### Night Sequence

No employee shall work more than three consecutive Night shifts.

---

### Night to Morning

Night followed immediately by Morning is prohibited.

---

### Operational Shift Count

Every employee shall receive exactly:

219 operational shifts.

---

### Weekend Ownership

No employee shall receive more than one designated Full Weekend Off within the same ten-week rotation cycle.

---

## 25.2 Soft Constraint Evaluation

The following objectives shall be measured.

- Standby to Morning transitions
- Isolated Off days
- Friday Night before designated Full Weekend Off
- Seven or more consecutive worked days
- Weekend shift balance
- Morning shift balance
- Afternoon shift balance
- Night shift balance
- Standby balance
- Holiday Worked Score balance
- Premium Holiday balance
- Shift Weight balance
- Pairing Diversity

---

## 25.3 Acceptance Criteria

A roster is acceptable when:

- All hard constraints pass.
- Operational shifts equal 219 per employee.
- Morning, Afternoon and Night allocations remain within the preferred target range of 71–75 where operationally achievable.
- Weekend operational shift variance does not exceed ±1 from the team average where operationally achievable.
- Fairness Index is as high as practical.
- Roster Quality Score is maximised.

---

# 26. Optimisation Hierarchy

The optimisation process shall apply objectives in the following order.

Priority 1

Hard Constraints

---

Priority 2

Fatigue Management

Including:

- Maximum consecutive Nights
- Night to Morning prohibition
- Standby to Morning avoidance
- Consecutive work block management

---

Priority 3

Operational Shift Target

Exactly:

219 operational shifts per employee.

---

Priority 4

Public Holiday Fairness

Minimise Holiday Worked Score variance.

---

Priority 5

Weekend Fairness

Balance weekend operational shifts.

Target:

±1 from the team average.

---

Priority 6

Shift-Type Fairness

Maintain Morning, Afternoon and Night shift allocations within the preferred target range of:

71–75

where operationally achievable.

---

Priority 7

Shift Weight Fairness

Minimise Shift Weight Score variance.

---

Priority 8

Weekend Ownership

Distribute designated Full Weekend Off allocations fairly.

---

Priority 9

Pairing Diversity

Maximise pairing diversity across all Group A and Group B employees.

---

Priority 10

Roster Quality Score

Maximise RQS after satisfying all higher-priority objectives.

---

# 27. Governing Principle

This specification is the governing document for the generation and validation of the Network Operations Centre annual roster.

Where any conflict exists between optimisation objectives, precedence shall always be determined by the Optimisation Hierarchy defined in Section 26.

Hard constraints shall never be violated in order to improve fairness or roster quality.

Soft constraints shall be optimised only after all hard constraints have been satisfied.

Operational continuity and safe staffing shall always take precedence over all other objectives.

---

# End of Document
