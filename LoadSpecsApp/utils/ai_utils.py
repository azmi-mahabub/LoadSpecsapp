"""
AI utilities for task prioritization and analysis
"""

from datetime import datetime, timedelta
from django.utils import timezone
import numpy as np


class TaskPrioritizer:
    """
    AI-based task priority analyzer using heuristic algorithms
    """
    
    def __init__(self):
        self.priority_weights = {
            'deadline_urgency': 0.35,
            'task_complexity': 0.20,
            'employee_workload': 0.25,
            'task_dependencies': 0.20
        }
    
    def analyze_task(self, task):
        """
        Analyze a task and suggest priority adjustment
        
        Returns:
            dict with suggested_priority, reason, and confidence_score
        """
        try:
            # Calculate various factors
            deadline_score = self._calculate_deadline_urgency(task)
            complexity_score = self._estimate_complexity(task)
            workload_score = self._calculate_employee_workload(task)
            
            # Calculate weighted priority score (0-100)
            priority_score = (
                deadline_score * self.priority_weights['deadline_urgency'] +
                complexity_score * self.priority_weights['task_complexity'] +
                workload_score * self.priority_weights['employee_workload']
            )
            
            # Determine suggested priority
            suggested_priority = self._score_to_priority(priority_score)
            
            # Generate reason
            reason = self._generate_reason(
                task, 
                deadline_score, 
                complexity_score, 
                workload_score,
                suggested_priority
            )
            
            # Calculate confidence (based on data availability)
            confidence_score = self._calculate_confidence(task)
            
            return {
                'suggested_priority': suggested_priority,
                'reason': reason,
                'confidence_score': confidence_score,
                'priority_score': priority_score
            }
        
        except Exception as e:
            print(f"Error analyzing task {task.id}: {e}")
            return None
    
    def _calculate_deadline_urgency(self, task):
        """
        Calculate urgency based on deadline (0-100 score)
        """
        days_until_due = (task.due_date - timezone.now().date()).days
        
        if days_until_due < 0:
            return 100  # Overdue - critical
        elif days_until_due <= 2:
            return 90  # Very urgent
        elif days_until_due <= 7:
            return 70  # Urgent
        elif days_until_due <= 14:
            return 50  # Moderate
        elif days_until_due <= 30:
            return 30  # Low urgency
        else:
            return 10  # Very low urgency
    
    def _estimate_complexity(self, task):
        """
        Estimate task complexity based on description length and keywords (0-100)
        """
        description = task.description or ''
        title = task.title or ''
        
        # Simple heuristic: longer descriptions = more complex
        text_length = len(description) + len(title)
        
        # Keyword analysis
        complex_keywords = [
            'implement', 'develop', 'architect', 'design', 'integrate',
            'analyze', 'research', 'optimize', 'refactor', 'migration'
        ]
        
        simple_keywords = [
            'update', 'fix', 'change', 'modify', 'review', 'check'
        ]
        
        text_lower = (description + title).lower()
        
        complexity_score = 50  # Base score
        
        # Adjust based on keywords
        for keyword in complex_keywords:
            if keyword in text_lower:
                complexity_score += 5
        
        for keyword in simple_keywords:
            if keyword in text_lower:
                complexity_score -= 3
        
        # Adjust based on length
        if text_length > 500:
            complexity_score += 20
        elif text_length > 200:
            complexity_score += 10
        elif text_length < 50:
            complexity_score -= 10
        
        return max(0, min(100, complexity_score))
    
    def _calculate_employee_workload(self, task):
        """
        Calculate employee's current workload (0-100 score)
        """
        employee = task.assigned_to
        
        # Get active tasks
        active_tasks = employee.tasks.filter(
            status__in=['pending', 'in_progress']
        ).exclude(id=task.id)
        
        active_count = active_tasks.count()
        
        # Get high priority tasks
        high_priority_count = active_tasks.filter(priority='high').count()
        
        # Calculate workload score
        workload_score = (active_count * 10) + (high_priority_count * 15)
        
        return min(100, workload_score)
    
    def _score_to_priority(self, score):
        """
        Convert numerical score to priority level
        """
        if score >= 70:
            return 'high'
        elif score >= 40:
            return 'medium'
        else:
            return 'low'
    
    def _generate_reason(self, task, deadline_score, complexity_score, workload_score, suggested_priority):
        """
        Generate human-readable reason for priority suggestion
        """
        reasons = []
        
        # Deadline reasoning
        if deadline_score >= 90:
            reasons.append("Task deadline is imminent or overdue")
        elif deadline_score >= 70:
            reasons.append("Task is due within a week")
        elif deadline_score <= 20:
            reasons.append("Deadline is far in the future")
        
        # Complexity reasoning
        if complexity_score >= 70:
            reasons.append("Task appears highly complex")
        elif complexity_score >= 50:
            reasons.append("Task has moderate complexity")
        
        # Workload reasoning
        if workload_score >= 70:
            reasons.append("Employee has high workload")
        elif workload_score >= 40:
            reasons.append("Employee has moderate workload")
        
        # Priority change reasoning
        current_priority = task.priority
        if suggested_priority != current_priority:
            if suggested_priority == 'high':
                reasons.append("Recommend upgrading to HIGH priority")
            elif suggested_priority == 'low':
                reasons.append("Consider downgrading to LOW priority")
        
        return ". ".join(reasons) + "."
    
    def _calculate_confidence(self, task):
        """
        Calculate confidence score based on available data
        """
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if task.description and len(task.description) > 50:
            confidence += 0.2
        
        if task.assigned_to.tasks.count() > 5:
            confidence += 0.15
        
        if task.team.tasks.count() > 10:
            confidence += 0.15
        
        return min(1.0, confidence)


class BurnoutPredictor:
    """
    Predict burnout risk for employees
    """
    
    @staticmethod
    def predict_burnout_trend(employee, weeks=4):
        """
        Predict burnout trend for the next few weeks
        
        Returns:
            dict with prediction, risk_level, and recommendation
        """
        from LoadSpecsApp.models import MoodCheckin
        
        # Get mood history
        mood_history = MoodCheckin.objects.filter(
            employee=employee
        ).order_by('-timestamp')[:28]  # Last 4 weeks
        
        if mood_history.count() < 7:
            return {
                'prediction': 'Insufficient data',
                'risk_level': 'unknown',
                'recommendation': 'Need at least 1 week of mood check-ins'
            }
        
        # Calculate mood scores
        mood_scores = {
            'happy': 1,
            'neutral': 2,
            'stressed': 3,
            'burnout': 4
        }
        
        scores = [mood_scores[mood.mood] for mood in mood_history]
        
        # Calculate trend (simple linear regression)
        if len(scores) >= 7:
            x = np.arange(len(scores))
            y = np.array(scores)
            
            # Calculate trend line
            z = np.polyfit(x, y, 1)
            slope = z[0]
            
            # Predict future trend
            if slope > 0.1:
                risk_level = 'increasing'
                prediction = 'Burnout risk is increasing'
                recommendation = 'Consider workload reduction and wellness support'
            elif slope < -0.1:
                risk_level = 'decreasing'
                prediction = 'Burnout risk is decreasing'
                recommendation = 'Continue current support measures'
            else:
                risk_level = 'stable'
                prediction = 'Burnout risk is stable'
                recommendation = 'Maintain regular monitoring'
            
            # Check current state
            recent_avg = np.mean(scores[:7])  # Last week
            if recent_avg >= 3.5:
                risk_level = 'high'
                recommendation = 'Immediate intervention recommended'
            
            return {
                'prediction': prediction,
                'risk_level': risk_level,
                'recommendation': recommendation,
                'trend_slope': float(slope),
                'current_score': float(recent_avg)
            }
        
        return {
            'prediction': 'Insufficient data for trend analysis',
            'risk_level': 'unknown',
            'recommendation': 'Continue regular check-ins'
        }


class ProductivityAnalyzer:
    """
    Analyze team and individual productivity
    """
    
    @staticmethod
    def calculate_team_productivity(team, days=30):
        """
        Calculate team productivity metrics
        """
        from django.db.models import Count, Q
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        # Get tasks in the period
        total_tasks = team.tasks.filter(created_at__gte=start_date).count()
        completed_tasks = team.tasks.filter(
            created_at__gte=start_date,
            status='completed'
        ).count()
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average time to complete
        completed_with_dates = team.tasks.filter(
            status='completed',
            updated_at__gte=start_date
        )
        
        avg_completion_time = 0
        if completed_with_dates.exists():
            times = [
                (task.updated_at.date() - task.created_at.date()).days
                for task in completed_with_dates
            ]
            avg_completion_time = np.mean(times) if times else 0
        
        # Productivity score (0-100)
        productivity_score = (
            completion_rate * 0.7 +  # Completion rate is most important
            (100 - min(avg_completion_time, 30) / 30 * 100) * 0.3  # Faster = better
        )
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completion_rate, 2),
            'avg_completion_time_days': round(avg_completion_time, 1),
            'productivity_score': round(productivity_score, 2)
        }
    
    @staticmethod
    def calculate_employee_productivity(employee, days=30):
        """
        Calculate individual employee productivity
        """
        start_date = timezone.now() - timedelta(days=days)
        
        total_tasks = employee.tasks.filter(created_at__gte=start_date).count()
        completed_tasks = employee.tasks.filter(
            created_at__gte=start_date,
            status='completed'
        ).count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Get burnout score
        burnout_score = employee.calculate_burnout_score()
        
        # Adjust productivity based on burnout
        adjusted_productivity = completion_rate * (1 - burnout_score / 200)
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completion_rate, 2),
            'burnout_score': burnout_score,
            'adjusted_productivity': round(adjusted_productivity, 2)
        }
