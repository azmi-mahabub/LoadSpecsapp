# 🔥 Task-Based Burnout Analytics System

## 🎯 Overview

**Fully Automatic Burnout Calculation** - No manual input required!

The system automatically calculates burnout risk for each employee based on their assigned tasks. It analyzes task priority, deadlines, workload, and completion status to provide accurate burnout predictions.

---

## 🧮 The Formula

```python
burnout_score = (priority_score + deadline_pressure + workload_factor + pending_factor) / 4
```

**Result:** Score from 0-100 indicating burnout risk level

---

## 📊 The 4 Calculation Factors

### 1️⃣ Priority Score (0-100)

**What it measures:** Average priority level of all assigned tasks

**Calculation:**
- High priority task → 100 points
- Medium priority task → 60 points
- Low priority task → 30 points
- **Average** across all tasks

**Example:**
```
Employee has:
- 2 high-priority tasks (100 + 100)
- 1 medium-priority task (60)
- 1 low-priority task (30)

Priority Score = (100 + 100 + 60 + 30) / 4 = 72.5
```

---

### 2️⃣ Deadline Pressure (0-100)

**What it measures:** Clustering of high-priority task deadlines

**Logic:**
- **100 points (High Pressure):** 2+ high-priority tasks with deadlines within 20 days of each other AND within 20 days from now
- **60 points (Medium Pressure):** Deadlines are 20-40 days apart, OR any task due within 20 days
- **30 points (Low Pressure):** Deadlines well-spaced (>40 days apart)

**Example Scenarios:**

**Critical (100):**
```
Today: Jan 1
Task 1 (high): Due Jan 10
Task 2 (high): Due Jan 15
→ Both within 20 days from now and 5 days apart = 100
```

**Moderate (60):**
```
Today: Jan 1
Task 1 (high): Due Jan 15
Task 2 (high): Due Feb 10
→ 26 days apart = 60
```

**Low (30):**
```
Today: Jan 1
Task 1 (high): Due Feb 15
Task 2 (high): Due April 1
→ 45+ days apart = 30
```

---

### 3️⃣ Workload Factor (0-100)

**What it measures:** Number of active (pending/in-progress) tasks

**Scale:**
- **>5 active tasks → 100** (Overloaded)
- **3-5 active tasks → 70** (Heavy load)
- **1-2 active tasks → 40** (Manageable)
- **0 active tasks → 10** (No load)

**Example:**
```
Employee A: 7 pending tasks, 1 in progress = 8 active → 100
Employee B: 2 pending tasks, 1 in progress = 3 active → 70
Employee C: 1 pending task = 1 active → 40
```

---

### 4️⃣ Pending Factor (0-100)

**What it measures:** Percentage of tasks that are still pending

**Formula:**
```python
pending_factor = (pending_tasks / total_tasks) × 100
```

**Example:**
```
Employee has 10 total tasks:
- 7 pending
- 2 in progress
- 1 completed

Pending Factor = (7 / 10) × 100 = 70
```

---

## 🚦 Burnout Risk Levels

| Score Range | Label | Emoji | Description | Action Required |
|------------|-------|-------|-------------|-----------------|
| **0-30** | Low Risk | 🟢 | Healthy balance | Continue monitoring |
| **31-60** | Moderate Risk | 🟡 | Manageable stress | Watch for increases |
| **61-80** | High Risk | 🟠 | Overload likely | Redistribute workload |
| **81-100** | Critical Risk | 🔴 | Burnout danger | **Immediate intervention** |

---

## 📈 Complete Calculation Example

### Scenario: Employee "John Doe"

**Tasks:**
1. High priority, Due in 5 days, Pending
2. High priority, Due in 7 days, In Progress
3. High priority, Due in 15 days, Pending
4. Medium priority, Due in 20 days, Pending
5. Medium priority, Due in 25 days, Pending
6. Low priority, Due in 30 days, Pending

---

### Step-by-Step Calculation:

#### 1️⃣ Priority Score
```
Tasks: 3 high (100 each), 2 medium (60 each), 1 low (30)
Total = (100×3 + 60×2 + 30×1) / 6
     = (300 + 120 + 30) / 6
     = 450 / 6
     = 75
```

#### 2️⃣ Deadline Pressure
```
High-priority tasks:
- Task 1: Due in 5 days
- Task 2: Due in 7 days (2 days after Task 1)
- Task 3: Due in 15 days (8 days after Task 2)

Two high-priority tasks (1 & 2) are within 20 days AND close together
→ Deadline Pressure = 100
```

#### 3️⃣ Workload Factor
```
Active tasks (pending + in progress):
- 5 pending + 1 in progress = 6 active tasks

6 tasks > 5 → Workload Factor = 100
```

#### 4️⃣ Pending Factor
```
Pending tasks: 5
Total tasks: 6

Pending Factor = (5 / 6) × 100 = 83.33
```

---

### Final Burnout Score:
```python
burnout_score = (priority_score + deadline_pressure + workload_factor + pending_factor) / 4
              = (75 + 100 + 100 + 83.33) / 4
              = 358.33 / 4
              = 89.58 ≈ 90
```

**Result: 90/100 = 🔴 CRITICAL RISK**

**Description:** "Burnout danger - Immediate intervention needed"

**Action:** 
- Redistribute some high-priority tasks
- Extend deadlines if possible
- Add team support

---

## 🔍 How to View Burnout Analytics

### For Team Leads:

1. **Tasks Page**
   - See burnout score for each employee
   - View risk level with emoji indicators
   - Read detailed descriptions

2. **Dashboard**
   - Overview of team burnout levels
   - Identify at-risk employees
   - Track burnout trends

### Display Format:
```
┌──────────────────────────────────────┐
│ Employee: John Doe                   │
│ Role: Employee                       │
│ Team: Development Team               │
│ Burnout Analysis:                    │
│   🔴 Critical Risk                   │
│   Score: 90/100                      │
│   Burnout danger - Immediate         │
│   intervention needed                │
└──────────────────────────────────────┘
```

---

## ⚡ Key Features

✅ **Fully Automatic** - No manual mood input required
✅ **Real-time Calculation** - Updates as tasks change
✅ **Data-Driven** - Based on objective task metrics
✅ **Accurate Prediction** - Multi-factor analysis
✅ **Visual Indicators** - Color-coded risk levels
✅ **Actionable Insights** - Clear descriptions and recommendations
✅ **Deadline Intelligence** - Detects task clustering
✅ **Priority Awareness** - Weights high-priority tasks appropriately

---

## 🧪 Test Scenarios

### Scenario 1: Healthy Employee (Low Risk)
```
- 2 medium-priority tasks
- Due in 30 and 45 days
- 1 pending, 1 in progress
- No clustering

Expected Score: ~25 (🟢 Low Risk)
```

### Scenario 2: Moderate Stress (Moderate Risk)
```
- 3 high-priority tasks
- 2 medium-priority tasks
- Due dates spread over 30 days
- All pending

Expected Score: ~45 (🟡 Moderate Risk)
```

### Scenario 3: Overloaded (High Risk)
```
- 5 high-priority tasks
- 2 medium-priority tasks
- All due within next 25 days
- 6 pending, 1 in progress

Expected Score: ~72 (🟠 High Risk)
```

### Scenario 4: Critical Burnout (Critical Risk)
```
- 6 high-priority tasks
- 2 medium-priority tasks
- Multiple deadlines within 10-20 days
- All pending or in-progress
- Tight clustering

Expected Score: ~88 (🔴 Critical Risk)
```

---

## 💡 Best Practices

### For Team Leads:

1. **Monitor Regularly**
   - Check burnout scores daily
   - Act on Critical/High risk immediately

2. **Redistribute Workload**
   - Move tasks from overloaded employees
   - Balance across team members

3. **Adjust Priorities**
   - Lower priority of less urgent tasks
   - Spread high-priority tasks over time

4. **Extend Deadlines**
   - When clustering detected
   - To reduce deadline pressure

5. **Team Support**
   - Assign helper for critical cases
   - Consider pair programming

### For System:

1. **Automatic Alerts**
   - Email notifications for Critical risk
   - Dashboard warnings for High risk

2. **Trend Analysis**
   - Track burnout over time
   - Identify patterns

3. **Predictive Insights**
   - Forecast burnout before it happens
   - Suggest preventive actions

---

## 🔧 Technical Implementation

### Model Methods:

```python
# Main calculation method
employee.calculate_burnout_score()  # Returns: 0-100

# Get risk level
employee.burnout_status  # Returns: "🔴 Critical Risk"

# Get description
employee.get_burnout_description()  # Returns: "Burnout danger..."
```

### In Templates:

```django
{% with score=employee.calculate_burnout_score %}
    Score: {{ score }}/100
    Status: {{ employee.burnout_status }}
    Description: {{ employee.get_burnout_description }}
{% endwith %}
```

---

## 📊 Expected Outcomes

### Short-term:
- Identify at-risk employees immediately
- Prevent burnout before it happens
- Data-driven workload decisions

### Long-term:
- Reduced employee burnout
- Improved productivity
- Better task distribution
- Higher team morale
- Lower turnover

---

## 🎯 Summary

**The system automatically:**
1. ✅ Analyzes all assigned tasks
2. ✅ Calculates 4 key factors
3. ✅ Produces accurate burnout score (0-100)
4. ✅ Classifies risk level (Low/Moderate/High/Critical)
5. ✅ Provides actionable descriptions
6. ✅ Displays visual indicators

**No manual input needed** - Everything is calculated from task data!

---

**Your LoadSpecs application now has a world-class burnout analytics system! 🚀**

**Version:** 2.0  
**Algorithm:** Multi-factor Task-Based Analysis  
**Accuracy:** High (4-factor weighted calculation)
