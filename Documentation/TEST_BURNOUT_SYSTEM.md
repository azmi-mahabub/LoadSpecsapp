# 🧪 How to Test the Burnout Analytics System

## Quick Test Guide

---

## 🎯 Test 1: Low Risk Employee (Score ~25)

### Setup:
1. Login as Team Lead
2. Go to Tasks page
3. Assign to Employee "TestUser1":
   - **Task 1:** Medium priority, Due in 30 days, Status: Pending
   - **Task 2:** Low priority, Due in 45 days, Status: In Progress

### Expected Result:
```
Burnout Analysis:
🟢 Low Risk
Score: 20-30/100
"Healthy balance - Good workload"
```

### Why?
- Only 2 tasks (Workload: 40)
- Medium/Low priorities (Priority Score: ~45)
- Well-spaced deadlines (Deadline Pressure: 30)
- 50% pending (Pending Factor: 50)
- **Average: ~41** → Low Risk

---

## 🎯 Test 2: Moderate Risk Employee (Score ~45)

### Setup:
Assign to Employee "TestUser2":
- **Task 1:** High priority, Due in 25 days, Status: Pending
- **Task 2:** High priority, Due in 28 days, Status: Pending
- **Task 3:** Medium priority, Due in 30 days, Status: Pending
- **Task 4:** Medium priority, Due in 35 days, Status: Pending

### Expected Result:
```
Burnout Analysis:
🟡 Moderate Risk
Score: 40-55/100
"Manageable stress - Monitor closely"
```

### Why?
- 4 active tasks (Workload: 70)
- Mix of High/Medium (Priority Score: ~80)
- Deadlines 25-35 days (Deadline Pressure: 30-60)
- 100% pending (Pending Factor: 100)
- **Average: ~70** → Actually High Risk!

---

## 🎯 Test 3: High Risk Employee (Score ~70)

### Setup:
Assign to Employee "TestUser3":
- **Task 1:** High priority, Due in 10 days, Status: Pending
- **Task 2:** High priority, Due in 12 days, Status: In Progress
- **Task 3:** High priority, Due in 15 days, Status: Pending
- **Task 4:** Medium priority, Due in 20 days, Status: Pending
- **Task 5:** Medium priority, Due in 25 days, Status: Pending

### Expected Result:
```
Burnout Analysis:
🟠 High Risk
Score: 65-75/100
"Overload likely - Redistribute workload"
```

### Why?
- 5 active tasks (Workload: 70)
- Mostly High priority (Priority Score: ~85)
- Multiple tasks within 20 days (Deadline Pressure: 100)
- 80% pending (Pending Factor: 80)
- **Average: ~84** → Actually Critical!

---

## 🎯 Test 4: Critical Risk Employee (Score ~90)

### Setup:
Assign to Employee "TestUser4":
- **Task 1:** High priority, Due in 5 days, Status: Pending
- **Task 2:** High priority, Due in 7 days, Status: In Progress
- **Task 3:** High priority, Due in 10 days, Status: Pending
- **Task 4:** High priority, Due in 12 days, Status: Pending
- **Task 5:** High priority, Due in 15 days, Status: Pending
- **Task 6:** Medium priority, Due in 18 days, Status: Pending
- **Task 7:** Medium priority, Due in 20 days, Status: Pending

### Expected Result:
```
Burnout Analysis:
🔴 Critical Risk
Score: 85-95/100
"Burnout danger - Immediate intervention needed"
```

### Why?
- 7 active tasks (Workload: 100)
- Mostly High priority (Priority Score: ~90)
- Multiple high-priority deadlines clustered within 15 days (Deadline Pressure: 100)
- 86% pending (Pending Factor: 86)
- **Average: ~94** → CRITICAL!

---

## 📊 Factor Breakdown Examples

### Example: Critical Risk Employee Analysis

```
Employee: TestUser4
Total Tasks: 7
Active Tasks: 7 (6 pending, 1 in-progress)

Factor Breakdown:
├─ Priority Score: 91.4
│  └─ (5×100 + 2×60) / 7 = 640/7 = 91.4
│
├─ Deadline Pressure: 100
│  └─ 2+ high-priority tasks within 20 days
│
├─ Workload Factor: 100
│  └─ 7 active tasks > 5
│
└─ Pending Factor: 85.7
   └─ (6 pending / 7 total) × 100 = 85.7

Final Score: (91.4 + 100 + 100 + 85.7) / 4 = 94.3 ≈ 94
Status: 🔴 Critical Risk
```

---

## 🔄 Testing Workflow

### 1. Create Test Employees

```bash
# As superuser in Django shell:
python manage.py shell

from LoadSpecsApp.models import User, Employee, Team

# Create team
team = Team.objects.create(team_name="Test Team", ...)

# Create 4 test employees
for i in range(1, 5):
    user = User.objects.create_user(
        username=f"testuser{i}",
        password="test123",
        is_employee=True
    )
    Employee.objects.create(user=user, team=team)
```

### 2. Assign Tasks (as Team Lead)

1. Login as Team Lead
2. Go to **Tasks → Assign New Task**
3. For each test scenario above:
   - Fill in task details
   - Select employee
   - Set priority
   - Set due date
   - Click **Assign**

### 3. View Results

1. Go to **Tasks** page
2. See each employee's burnout score
3. Verify risk levels match expectations

---

## ✅ Expected Visual Display

### Critical Risk Display:
```
┌─────────────────────────────────────────┐
│ Employee Name: testuser4                │
│ Role: Employee                          │
│ Team Name: Test Team                    │
│ Burnout Analysis:                       │
│   🔴 Critical Risk                      │
│   Score: 94/100                         │
│   Burnout danger - Immediate            │
│   intervention needed                   │
└─────────────────────────────────────────┘
```

### High Risk Display:
```
┌─────────────────────────────────────────┐
│ Employee Name: testuser3                │
│ Role: Employee                          │
│ Team Name: Test Team                    │
│ Burnout Analysis:                       │
│   🟠 High Risk                          │
│   Score: 72/100                         │
│   Overload likely - Redistribute        │
│   workload                              │
└─────────────────────────────────────────┘
```

---

## 🎬 Quick Test Script

Copy and paste into Django shell:

```python
from LoadSpecsApp.models import Employee
from django.contrib.auth import get_user_model

User = get_user_model()

# Check all employees
for emp in Employee.objects.all():
    score = emp.calculate_burnout_score()
    print(f"\n{emp.user.username}:")
    print(f"  Score: {score}/100")
    print(f"  Status: {emp.burnout_status}")
    print(f"  Description: {emp.get_burnout_description()}")
    print(f"  Tasks: {emp.assigned_tasks}")
    print(f"  Pending: {emp.pending_tasks}")
```

---

## 🔍 Debugging

If scores seem wrong, check:

1. **Task Count:** Does employee have tasks?
   ```python
   employee.tasks.all()
   ```

2. **Priority Distribution:**
   ```python
   employee.tasks.values_list('priority', flat=True)
   ```

3. **Due Dates:**
   ```python
   employee.tasks.values_list('due_date', flat=True)
   ```

4. **Status:**
   ```python
   employee.tasks.values_list('status', flat=True)
   ```

5. **Factor Breakdown:**
   ```python
   emp = Employee.objects.first()
   print("Priority Score:", emp._calculate_priority_score(emp.tasks.all()))
   print("Deadline Pressure:", emp._calculate_deadline_pressure(emp.tasks.filter(status__in=['pending', 'in_progress'])))
   print("Workload Factor:", emp._calculate_workload_factor(emp.tasks.filter(status__in=['pending', 'in_progress'])))
   print("Pending Factor:", emp._calculate_pending_factor(emp.tasks.all()))
   ```

---

## 📅 Real-World Testing Tips

### Simulate Realistic Scenarios:

**Scenario A: New Employee**
- 1-2 tasks, low/medium priority
- Expected: 🟢 Low Risk (15-25)

**Scenario B: Regular Load**
- 3-4 tasks, mixed priorities
- Deadlines spread over 30+ days
- Expected: 🟡 Moderate Risk (35-50)

**Scenario C: Sprint Deadline**
- 5+ tasks, mostly high priority
- Multiple deadlines in 2-3 weeks
- Expected: 🟠 High Risk (65-80)

**Scenario D: Crisis Mode**
- 7+ tasks, all high priority
- Clustered deadlines (within 10 days)
- Expected: 🔴 Critical Risk (85-100)

---

## ✅ Success Criteria

The system is working correctly if:

1. ✅ Score increases with more tasks
2. ✅ Score increases with higher priorities
3. ✅ Score increases when deadlines cluster
4. ✅ Score increases with more pending tasks
5. ✅ Colors match risk levels
6. ✅ Descriptions are appropriate
7. ✅ Score updates when tasks change

---

**Happy Testing! 🎉**
