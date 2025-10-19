from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Team, Task, MoodCheckin, Employee


class SignUpForm(UserCreationForm):
    """Custom signup form with role selection"""
    USER_TYPE_CHOICES = [
        ('employee', 'Employee'),
        ('team_lead', 'Team Lead'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'width: 200px;'
        }),
        label='Signup As'
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username (unique)',
            'autocomplete': 'off'
        }),
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'password1'
        }),
        help_text='Password must be at least 8 characters long.'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password',
            'id': 'password2'
        })
    )
    
    company_name_input = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your company name',
            'id': 'company_name_input'
        }),
        label='Company Name (for Team Leads)'
    )
    
    company_name_select = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'company_name_select'
        }),
        label='Select Company (for Employees)'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2', 'user_type']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get list of companies from existing team leads
        companies = User.objects.filter(
            is_team_lead=True, 
            company_name__isnull=False
        ).exclude(company_name='').values_list('company_name', flat=True).distinct()
        
        company_choices = [('', '-- Select a company --')] + [(c, c) for c in companies]
        self.fields['company_name_select'].choices = company_choices
    
    def clean_username(self):
        """Ensure username is unique"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose a different one.')
        return username
    
    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email
    
    def clean(self):
        """Additional validation"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        user_type = cleaned_data.get('user_type')
        company_input = cleaned_data.get('company_name_input')
        company_select = cleaned_data.get('company_name_select')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        # Validate company name based on user type
        if user_type == 'team_lead' and not company_input:
            raise forms.ValidationError('Team Leads must enter a company name.')
        
        if user_type == 'employee' and not company_select:
            raise forms.ValidationError('Employees must select a company.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        user_type = self.cleaned_data['user_type']
        if user_type == 'employee':
            user.is_employee = True
            user.company_name = self.cleaned_data.get('company_name_select')
        elif user_type == 'team_lead':
            user.is_team_lead = True
            user.company_name = self.cleaned_data.get('company_name_input')
        
        if commit:
            user.save()
            # Create corresponding profile
            if user.is_employee:
                Employee.objects.create(user=user)
            elif user.is_team_lead:
                from .models import TeamLead
                TeamLead.objects.create(user=user)
        
        return user


class LoginForm(AuthenticationForm):
    """Custom login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'User Name or Email Address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'bio', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'style': 'background-color: #e9ecef; cursor: not-allowed;'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make username field read-only
        self.fields['username'].disabled = True
        self.fields['username'].help_text = 'Username cannot be changed'


class TeamCreateForm(forms.ModelForm):
    """Form for creating a new team"""
    class Meta:
        model = Team
        fields = ['team_name', 'description']
        widgets = {
            'team_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Team description...'
            }),
        }


class JoinTeamForm(forms.Form):
    """Form for employees to join a team"""
    join_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter team join code'
        })
    )


class TaskCreateForm(forms.ModelForm):
    """Form for creating tasks"""
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'priority', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Task description...'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class TaskUpdateForm(forms.ModelForm):
    """Form for updating task status"""
    class Meta:
        model = Task
        fields = ['status', 'description']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }


class MoodCheckinForm(forms.ModelForm):
    """Form for mood check-ins"""
    class Meta:
        model = MoodCheckin
        fields = ['mood', 'notes']
        widgets = {
            'mood': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about your mood...'
            }),
        }
