"""
Comprehensive Linear Data Models

This module provides dataclass-based models for all Linear entities including
Issue, Team, User, WorkflowState, Project, Comment, etc. Each model includes
proper validation, serialization methods, and type safety.

Features:
- Type-safe dataclasses for all Linear entities
- JSON serialization/deserialization
- Data validation with custom validators
- Relationship handling between entities
- Enum types for standardized values
- Optional field handling
- DateTime parsing and formatting
- URL validation and formatting

Author: Stephen Thompson
"""

import json
import re
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union, Type, TypeVar, get_type_hints
from enum import Enum
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Type variable for generic model operations
T = TypeVar('T', bound='BaseLinearModel')


class ValidationError(Exception):
    """Exception raised for data validation errors."""
    pass


class SerializationError(Exception):
    """Exception raised for serialization/deserialization errors."""
    pass


# Enums for Linear entity types and states

class IssueState(Enum):
    """Linear issue states."""
    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"


class IssuePriority(Enum):
    """Linear issue priorities."""
    NO_PRIORITY = 0
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class WorkflowType(Enum):
    """Linear workflow state types."""
    BACKLOG = "backlog"
    UNSTARTED = "unstarted"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ProjectStatus(Enum):
    """Linear project statuses."""
    PLANNED = "planned"
    STARTED = "started"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELED = "canceled"


class UserStatus(Enum):
    """Linear user statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class CommentType(Enum):
    """Linear comment types."""
    COMMENT = "comment"
    SYSTEM = "system"


class AttachmentType(Enum):
    """Linear attachment types."""
    IMAGE = "image"
    FILE = "file"
    LINK = "link"


# Utility functions for validation and parsing

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not dt_str:
        return None
    
    try:
        # Handle various ISO formats
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        
        # Try parsing with timezone info
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            # Fallback: assume UTC if no timezone
            dt = datetime.fromisoformat(dt_str.replace('Z', ''))
            return dt.replace(tzinfo=timezone.utc)
    
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse datetime '{dt_str}': {e}")
        return None


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime object to ISO string."""
    if not dt:
        return None
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.isoformat()


def validate_linear_id(linear_id: str) -> bool:
    """Validate Linear ID format (UUID-like)."""
    if not linear_id or not isinstance(linear_id, str):
        return False
    
    # Linear IDs are typically UUIDs or similar format
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    return bool(re.match(pattern, linear_id, re.IGNORECASE))


def validate_team_key(team_key: str) -> bool:
    """Validate Linear team key format."""
    if not team_key or not isinstance(team_key, str):
        return False
    
    # Team keys are typically 2-5 uppercase letters
    pattern = r'^[A-Z]{2,5}$'
    return bool(re.match(pattern, team_key))


# Base model class with common functionality

@dataclass
class BaseLinearModel:
    """Base class for all Linear models with common functionality."""
    
    def validate(self) -> None:
        """Validate the model data."""
        # Override in subclasses for specific validation
        pass
    
    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary."""
        data = asdict(self)
        
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = format_datetime(value)
            elif isinstance(value, Enum):
                data[key] = value.value
            elif isinstance(value, BaseLinearModel):
                data[key] = value.to_dict(exclude_none)
            elif isinstance(value, list) and value and isinstance(value[0], BaseLinearModel):
                data[key] = [item.to_dict(exclude_none) for item in value]
        
        return data
    
    def to_json(self, exclude_none: bool = True, indent: Optional[int] = None) -> str:
        """Convert model to JSON string."""
        try:
            return json.dumps(self.to_dict(exclude_none), indent=indent, default=str)
        except (TypeError, ValueError) as e:
            raise SerializationError(f"Failed to serialize to JSON: {e}")
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create model instance from dictionary."""
        if not isinstance(data, dict):
            raise ValidationError(f"Expected dict, got {type(data)}")
        
        try:
            # Get type hints for the class
            hints = get_type_hints(cls)
            
            # Process the data according to field types
            processed_data = {}
            for field_name, field_type in hints.items():
                if field_name in data:
                    value = data[field_name]
                    processed_data[field_name] = cls._process_field_value(field_name, field_type, value)
            
            # Create instance
            instance = cls(**processed_data)
            instance.validate()
            return instance
        
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Failed to create {cls.__name__} from dict: {e}")
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Create model instance from JSON string."""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise SerializationError(f"Invalid JSON: {e}")
    
    @classmethod
    def _process_field_value(cls, field_name: str, field_type: Type, value: Any) -> Any:
        """Process field value according to its type."""
        if value is None:
            return None
        
        # Handle datetime fields
        if field_type == datetime or field_type == Optional[datetime]:
            return parse_datetime(value) if isinstance(value, str) else value
        
        # Handle enum fields
        if hasattr(field_type, '__bases__') and Enum in field_type.__bases__:
            if isinstance(value, str):
                # Try to find enum by value
                for enum_item in field_type:
                    if enum_item.value == value:
                        return enum_item
            return value
        
        # Handle nested models
        if hasattr(field_type, '__bases__') and BaseLinearModel in field_type.__bases__:
            if isinstance(value, dict):
                return field_type.from_dict(value)
            return value
        
        # Handle lists of models
        if hasattr(field_type, '__origin__') and field_type.__origin__ is list:
            if isinstance(value, list):
                item_type = field_type.__args__[0]
                if hasattr(item_type, '__bases__') and BaseLinearModel in item_type.__bases__:
                    return [item_type.from_dict(item) if isinstance(item, dict) else item for item in value]
        
        return value
    
    def __post_init__(self):
        """Post-initialization validation."""
        self.validate()


# Core Linear entity models

@dataclass
class LinearUser(BaseLinearModel):
    """Linear user model."""
    id: str
    name: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    status: Optional[UserStatus] = None
    timezone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    admin: bool = False
    guest: bool = False
    
    def validate(self) -> None:
        """Validate user data."""
        if not self.id:
            raise ValidationError("User ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid user ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("User name is required")
        
        if not self.email or not validate_email(self.email):
            raise ValidationError(f"Invalid email format: {self.email}")
        
        if self.avatar_url and not validate_url(self.avatar_url):
            raise ValidationError(f"Invalid avatar URL: {self.avatar_url}")


@dataclass
class LinearTeam(BaseLinearModel):
    """Linear team model."""
    id: str
    name: str
    key: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    private: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate team data."""
        if not self.id:
            raise ValidationError("Team ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid team ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("Team name is required")
        
        if not self.key or not validate_team_key(self.key):
            raise ValidationError(f"Invalid team key format: {self.key}")
        
        if self.color and not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
            raise ValidationError(f"Invalid color format: {self.color}")


@dataclass
class LinearWorkflowState(BaseLinearModel):
    """Linear workflow state model."""
    id: str
    name: str
    type: WorkflowType
    position: float
    color: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[str] = None
    
    def validate(self) -> None:
        """Validate workflow state data."""
        if not self.id:
            raise ValidationError("Workflow state ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid workflow state ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("Workflow state name is required")
        
        if not isinstance(self.type, WorkflowType):
            raise ValidationError(f"Invalid workflow type: {self.type}")
        
        if not isinstance(self.position, (int, float)):
            raise ValidationError(f"Position must be a number: {self.position}")
        
        if self.color and not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
            raise ValidationError(f"Invalid color format: {self.color}")
        
        if self.team_id and not validate_linear_id(self.team_id):
            raise ValidationError(f"Invalid team ID format: {self.team_id}")


@dataclass
class LinearLabel(BaseLinearModel):
    """Linear label model."""
    id: str
    name: str
    color: str
    description: Optional[str] = None
    team_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate label data."""
        if not self.id:
            raise ValidationError("Label ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid label ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("Label name is required")
        
        if not self.color or not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
            raise ValidationError(f"Invalid color format: {self.color}")
        
        if self.team_id and not validate_linear_id(self.team_id):
            raise ValidationError(f"Invalid team ID format: {self.team_id}")


@dataclass
class LinearProject(BaseLinearModel):
    """Linear project model."""
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator: Optional[LinearUser] = None
    lead: Optional[LinearUser] = None
    members: List[LinearUser] = field(default_factory=list)
    teams: List[LinearTeam] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate project data."""
        if not self.id:
            raise ValidationError("Project ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid project ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("Project name is required")
        
        if self.color and not re.match(r'^#[0-9A-Fa-f]{6}$', self.color):
            raise ValidationError(f"Invalid color format: {self.color}")
        
        if self.start_date and self.target_date and self.start_date > self.target_date:
            raise ValidationError("Start date cannot be after target date")


@dataclass
class LinearAttachment(BaseLinearModel):
    """Linear attachment model."""
    id: str
    title: str
    url: str
    subtitle: Optional[str] = None
    type: Optional[AttachmentType] = None
    size: Optional[int] = None
    created_at: Optional[datetime] = None
    creator: Optional[LinearUser] = None
    
    def validate(self) -> None:
        """Validate attachment data."""
        if not self.id:
            raise ValidationError("Attachment ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid attachment ID format: {self.id}")
        
        if not self.title or not self.title.strip():
            raise ValidationError("Attachment title is required")
        
        if not self.url or not validate_url(self.url):
            raise ValidationError(f"Invalid attachment URL: {self.url}")
        
        if self.size is not None and self.size < 0:
            raise ValidationError("Attachment size cannot be negative")


@dataclass
class LinearComment(BaseLinearModel):
    """Linear comment model."""
    id: str
    body: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[LinearUser] = None
    issue_id: Optional[str] = None
    type: CommentType = CommentType.COMMENT
    edited: bool = False
    
    def validate(self) -> None:
        """Validate comment data."""
        if not self.id:
            raise ValidationError("Comment ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid comment ID format: {self.id}")
        
        if not self.body or not self.body.strip():
            raise ValidationError("Comment body is required")
        
        if not self.created_at:
            raise ValidationError("Comment created_at is required")
        
        if self.issue_id and not validate_linear_id(self.issue_id):
            raise ValidationError(f"Invalid issue ID format: {self.issue_id}")


@dataclass
class LinearIssue(BaseLinearModel):
    """Linear issue model."""
    id: str
    identifier: str
    title: str
    description: Optional[str] = None
    priority: IssuePriority = IssuePriority.NO_PRIORITY
    estimate: Optional[float] = None
    url: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Relationships
    team: Optional[LinearTeam] = None
    state: Optional[LinearWorkflowState] = None
    creator: Optional[LinearUser] = None
    assignee: Optional[LinearUser] = None
    project: Optional[LinearProject] = None
    parent: Optional['LinearIssue'] = None
    labels: List[LinearLabel] = field(default_factory=list)
    comments: List[LinearComment] = field(default_factory=list)
    attachments: List[LinearAttachment] = field(default_factory=list)
    children: List['LinearIssue'] = field(default_factory=list)
    
    # Computed properties
    number: Optional[int] = None
    branch_name: Optional[str] = None
    
    def validate(self) -> None:
        """Validate issue data."""
        if not self.id:
            raise ValidationError("Issue ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid issue ID format: {self.id}")
        
        if not self.identifier or not self.identifier.strip():
            raise ValidationError("Issue identifier is required")
        
        # Validate identifier format (e.g., "ENG-123")
        if not re.match(r'^[A-Z]{2,5}-\d+$', self.identifier):
            raise ValidationError(f"Invalid identifier format: {self.identifier}")
        
        if not self.title or not self.title.strip():
            raise ValidationError("Issue title is required")
        
        if not isinstance(self.priority, IssuePriority):
            raise ValidationError(f"Invalid priority: {self.priority}")
        
        if self.estimate is not None and self.estimate < 0:
            raise ValidationError("Estimate cannot be negative")
        
        if self.url and not validate_url(self.url):
            raise ValidationError(f"Invalid issue URL: {self.url}")
        
        # Validate date relationships
        if self.started_at and self.created_at and self.started_at < self.created_at:
            raise ValidationError("Started date cannot be before created date")
        
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValidationError("Completed date cannot be before started date")
        
        if self.due_date and self.created_at and self.due_date < self.created_at:
            raise ValidationError("Due date cannot be before created date")
    
    @property
    def is_completed(self) -> bool:
        """Check if issue is completed."""
        return self.completed_at is not None or (
            self.state and self.state.type == WorkflowType.COMPLETED
        )
    
    @property
    def is_canceled(self) -> bool:
        """Check if issue is canceled."""
        return self.canceled_at is not None or (
            self.state and self.state.type == WorkflowType.CANCELED
        )
    
    @property
    def is_in_progress(self) -> bool:
        """Check if issue is in progress."""
        return self.started_at is not None and not self.is_completed and not self.is_canceled
    
    @property
    def age_days(self) -> Optional[int]:
        """Get issue age in days."""
        if not self.created_at:
            return None
        
        end_date = self.completed_at or self.canceled_at or datetime.now(timezone.utc)
        return (end_date - self.created_at).days
    
    def add_comment(self, comment: LinearComment) -> None:
        """Add a comment to the issue."""
        if comment not in self.comments:
            self.comments.append(comment)
            comment.issue_id = self.id
    
    def add_label(self, label: LinearLabel) -> None:
        """Add a label to the issue."""
        if label not in self.labels:
            self.labels.append(label)
    
    def remove_label(self, label: LinearLabel) -> None:
        """Remove a label from the issue."""
        if label in self.labels:
            self.labels.remove(label)
    
    def add_attachment(self, attachment: LinearAttachment) -> None:
        """Add an attachment to the issue."""
        if attachment not in self.attachments:
            self.attachments.append(attachment)


@dataclass
class LinearCycle(BaseLinearModel):
    """Linear cycle model."""
    id: str
    name: str
    number: int
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None
    team: Optional[LinearTeam] = None
    issues: List[LinearIssue] = field(default_factory=list)
    completed_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate cycle data."""
        if not self.id:
            raise ValidationError("Cycle ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid cycle ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("Cycle name is required")
        
        if not isinstance(self.number, int) or self.number < 1:
            raise ValidationError("Cycle number must be a positive integer")
        
        if not self.start_date or not self.end_date:
            raise ValidationError("Cycle start and end dates are required")
        
        if self.start_date >= self.end_date:
            raise ValidationError("Cycle start date must be before end date")
    
    @property
    def is_active(self) -> bool:
        """Check if cycle is currently active."""
        now = datetime.now(timezone.utc)
        return self.start_date <= now <= self.end_date and not self.completed_at
    
    @property
    def is_completed(self) -> bool:
        """Check if cycle is completed."""
        return self.completed_at is not None
    
    @property
    def duration_days(self) -> int:
        """Get cycle duration in days."""
        return (self.end_date - self.start_date).days


@dataclass
class LinearOrganization(BaseLinearModel):
    """Linear organization model."""
    id: str
    name: str
    url_key: str
    logo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    teams: List[LinearTeam] = field(default_factory=list)
    users: List[LinearUser] = field(default_factory=list)
    projects: List[LinearProject] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate organization data."""
        if not self.id:
            raise ValidationError("Organization ID is required")
        
        if not validate_linear_id(self.id):
            raise ValidationError(f"Invalid organization ID format: {self.id}")
        
        if not self.name or not self.name.strip():
            raise ValidationError("Organization name is required")
        
        if not self.url_key or not self.url_key.strip():
            raise ValidationError("Organization URL key is required")
        
        if self.logo_url and not validate_url(self.logo_url):
            raise ValidationError(f"Invalid logo URL: {self.logo_url}")


# Utility functions for working with models

def create_issue_from_api_data(api_data: Dict[str, Any]) -> LinearIssue:
    """Create a LinearIssue from Linear API response data."""
    try:
        # Extract nested objects
        team_data = api_data.pop('team', None)
        state_data = api_data.pop('state', None)
        creator_data = api_data.pop('creator', None)
        assignee_data = api_data.pop('assignee', None)
        project_data = api_data.pop('project', None)
        parent_data = api_data.pop('parent', None)
        labels_data = api_data.pop('labels', {}).get('nodes', [])
        comments_data = api_data.pop('comments', {}).get('nodes', [])
        attachments_data = api_data.pop('attachments', {}).get('nodes', [])
        
        # Create nested objects
        team = LinearTeam.from_dict(team_data) if team_data else None
        state = LinearWorkflowState.from_dict(state_data) if state_data else None
        creator = LinearUser.from_dict(creator_data) if creator_data else None
        assignee = LinearUser.from_dict(assignee_data) if assignee_data else None
        project = LinearProject.from_dict(project_data) if project_data else None
        parent = LinearIssue.from_dict(parent_data) if parent_data else None
        
        labels = [LinearLabel.from_dict(label_data) for label_data in labels_data]
        comments = [LinearComment.from_dict(comment_data) for comment_data in comments_data]
        attachments = [LinearAttachment.from_dict(att_data) for att_data in attachments_data]
        
        # Convert priority to enum
        priority_value = api_data.get('priority', 0)
        priority = IssuePriority(priority_value) if isinstance(priority_value, int) else IssuePriority.NO_PRIORITY
        
        # Create issue
        issue = LinearIssue(
            id=api_data['id'],
            identifier=api_data['identifier'],
            title=api_data['title'],
            description=api_data.get('description'),
            priority=priority,
            estimate=api_data.get('estimate'),
            url=api_data.get('url', ''),
            created_at=parse_datetime(api_data.get('createdAt')),
            updated_at=parse_datetime(api_data.get('updatedAt')),
            completed_at=parse_datetime(api_data.get('completedAt')),
            canceled_at=parse_datetime(api_data.get('canceledAt')),
            started_at=parse_datetime(api_data.get('startedAt')),
            due_date=parse_datetime(api_data.get('dueDate')),
            team=team,
            state=state,
            creator=creator,
            assignee=assignee,
            project=project,
            parent=parent,
            labels=labels,
            comments=comments,
            attachments=attachments,
            number=api_data.get('number'),
            branch_name=api_data.get('branchName')
        )
        
        return issue
    
    except Exception as e:
        raise ValidationError(f"Failed to create LinearIssue from API data: {e}")


def create_team_from_api_data(api_data: Dict[str, Any]) -> LinearTeam:
    """Create a LinearTeam from Linear API response data."""
    return LinearTeam(
        id=api_data['id'],
        name=api_data['name'],
        key=api_data['key'],
        description=api_data.get('description'),
        color=api_data.get('color'),
        icon=api_data.get('icon'),
        private=api_data.get('private', False),
        created_at=parse_datetime(api_data.get('createdAt')),
        updated_at=parse_datetime(api_data.get('updatedAt'))
    )


def create_user_from_api_data(api_data: Dict[str, Any]) -> LinearUser:
    """Create a LinearUser from Linear API response data."""
    status_str = api_data.get('status')
    status = None
    if status_str:
        try:
            status = UserStatus(status_str.lower())
        except ValueError:
            logger.warning(f"Unknown user status: {status_str}")
    
    return LinearUser(
        id=api_data['id'],
        name=api_data['name'],
        email=api_data['email'],
        display_name=api_data.get('displayName'),
        avatar_url=api_data.get('avatarUrl'),
        status=status,
        timezone=api_data.get('timezone'),
        created_at=parse_datetime(api_data.get('createdAt')),
        updated_at=parse_datetime(api_data.get('updatedAt')),
        active=api_data.get('active', True),
        admin=api_data.get('admin', False),
        guest=api_data.get('guest', False)
    )


def create_workflow_state_from_api_data(api_data: Dict[str, Any]) -> LinearWorkflowState:
    """Create a LinearWorkflowState from Linear API response data."""
    workflow_type = WorkflowType(api_data['type'].lower())
    
    return LinearWorkflowState(
        id=api_data['id'],
        name=api_data['name'],
        type=workflow_type,
        position=api_data['position'],
        color=api_data.get('color'),
        description=api_data.get('description'),
        team_id=api_data.get('teamId')
    )


def batch_validate_models(models: List[BaseLinearModel]) -> List[str]:
    """Validate a batch of models and return list of validation errors."""
    errors = []
    
    for i, model in enumerate(models):
        try:
            model.validate()
        except ValidationError as e:
            errors.append(f"Model {i} ({type(model).__name__}): {e}")
    
    return errors


def serialize_models_to_json(models: List[BaseLinearModel], indent: Optional[int] = 2) -> str:
    """Serialize a list of models to JSON."""
    try:
        data = [model.to_dict() for model in models]
        return json.dumps(data, indent=indent, default=str)
    except Exception as e:
        raise SerializationError(f"Failed to serialize models: {e}")


def deserialize_models_from_json(json_str: str, model_class: Type[T]) -> List[T]:
    """Deserialize a list of models from JSON."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            raise ValidationError("Expected JSON array")
        
        return [model_class.from_dict(item) for item in data]
    except json.JSONDecodeError as e:
        raise SerializationError(f"Invalid JSON: {e}")


# Export all models and utilities
__all__ = [
    # Enums
    'IssueState', 'IssuePriority', 'WorkflowType', 'ProjectStatus', 
    'UserStatus', 'CommentType', 'AttachmentType',
    
    # Models
    'BaseLinearModel', 'LinearUser', 'LinearTeam', 'LinearWorkflowState',
    'LinearLabel', 'LinearProject', 'LinearAttachment', 'LinearComment',
    'LinearIssue', 'LinearCycle', 'LinearOrganization',
    
    # Exceptions
    'ValidationError', 'SerializationError',
    
    # Utility functions
    'validate_email', 'validate_url', 'parse_datetime', 'format_datetime',
    'validate_linear_id', 'validate_team_key',
    'create_issue_from_api_data', 'create_team_from_api_data',
    'create_user_from_api_data', 'create_workflow_state_from_api_data',
    'batch_validate_models', 'serialize_models_to_json', 'deserialize_models_from_json'
]