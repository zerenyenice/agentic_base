# Standard Development Workflow

## 1. Purpose

This workflow standardizes the software development process from project initiation to merging completed work into the `master` branch and triggering the automated deployment process.

The DevOps/Platform Team owns the workflow definition, governance, templates, automation, and continuous improvement.

## 2. Workflow Overview

The standard development workflow consists of the following stages:

1. Create and approve the Product Requirements Document.
2. Convert approved requirements into Azure Boards work items.
3. Refine, prioritize, and assign development tasks.
4. Create a dedicated Git branch for each task.
5. Implement and test the required changes.
6. Open a pull request to the `master` branch.
7. Review and validate the pull request.
8. Merge the approved pull request.
9. Trigger the automated deployment process.

# 3. Product Requirements Document

## 3.1 PRD Purpose

A Product Requirements Document must be created for every project before development work begins.

The PRD acts as the primary source of truth for:

* Business requirements
* Solution design
* Development planning
* Testing
* Acceptance
* Deployment
* Operations

The PRD should include:

* Business problem and background
* Project objectives
* Stakeholders and users
* Scope and exclusions
* Functional requirements
* Non-functional requirements
* User workflows and use cases
* Integration and data requirements
* Security and compliance requirements
* Deployment and operational requirements
* Assumptions, constraints, and dependencies
* Risks
* Acceptance criteria
* Open questions and decisions

The PRD must be reviewed and approved before Azure Boards work items are created.

Changes made after approval must be versioned and reflected in the related work items.

## 3.2 PRD Ownership and Collaboration

The PRD is developed collaboratively by the following roles:

### Project Manager

The Project Manager:

* Coordinates the PRD creation process
* Organizes stakeholder meetings
* Manages scope and expectations
* Tracks open questions
* Coordinates reviews and approvals
* Ensures alignment between stakeholders and the project team

### Subject Matter Expert

The Subject Matter Expert:

* Describes the current business process
* Defines domain rules
* Identifies user needs
* Documents business exceptions
* Validates functional requirements
* Defines expected business outcomes

### AI Architect

The AI Architect:

* Defines the AI solution design
* Defines agent behavior and responsibilities
* Identifies model interactions
* Designs data and information flows
* Defines evaluation requirements
* Identifies AI-specific risks and constraints
* Validates the technical feasibility of the AI solution

### DevOps Engineer

The DevOps Engineer:

* Defines infrastructure requirements
* Defines environment requirements
* Defines CI/CD requirements
* Identifies security and network requirements
* Defines observability requirements
* Defines deployment and operational requirements
* Identifies infrastructure-related dependencies and constraints

All contributors are responsible for reviewing the complete PRD, not only the sections related to their own expertise.

The Project Manager coordinates the final review and ensures that unresolved questions are documented before approval.

## 3.3 PRD Preparation Workflow

### Step 1: Requirement Discovery

The Project Manager organizes discovery sessions with the relevant stakeholders.

During these sessions, the project team collects:

* Business problems and objectives
* Current business processes
* User roles and expectations
* Functional requirements
* Business rules and exceptions
* Data sources and integrations
* Security and compliance requirements
* Expected outputs
* Success criteria

### Step 2: Initial PRD Draft

The Project Manager creates the initial PRD structure and coordinates contributions from the Subject Matter Expert, AI Architect, and DevOps Engineer.

Each role contributes to the sections related to its area of expertise.

### Step 3: Collaborative Review

The project team reviews the complete PRD together to:

* Identify missing requirements
* Resolve conflicting expectations
* Validate technical feasibility
* Clarify assumptions
* Identify dependencies
* Document unresolved questions
* Define measurable acceptance criteria

### Step 4: Stakeholder Validation

The PRD is presented to the customer or relevant business stakeholders for validation.

Stakeholder feedback must be reviewed and incorporated before final approval.

### Step 5: PRD Approval

The PRD must be approved before development work items are created.

The approved PRD should include:

* Document version
* Approval date
* Approvers
* Remaining assumptions
* Accepted risks
* Open items that do not block development

### Step 6: PRD Change Management

Changes made after approval must be documented.

Each significant change should include:

* Change description
* Reason for the change
* Impact on scope
* Impact on schedule
* Impact on architecture or infrastructure
* Related Azure Boards work items
* Approval status

# 4. Azure Boards Work-Item Structure

After PRD approval, requirements are converted into Azure Boards work items.

The standard hierarchy is:

```text
PRD → Epic → Feature → User Story → Task
```

## 4.1 Epic

An Epic represents a major business objective, product capability, or project-level outcome.

An Epic should:

* Align with a major PRD objective
* Contain one or more Features
* Describe the expected business outcome
* Avoid implementation-level details

A project may contain one or more Epics depending on its scope.

## 4.2 Feature

A Feature represents a significant functional or technical capability required to deliver an Epic.

A Feature should:

* Be linked to one Epic
* Represent a meaningful product capability
* Be deliverable through multiple User Stories
* Reference the relevant PRD section
* Include clear acceptance conditions

Example Features may include:

* Authentication
* Data ingestion
* Invoice processing
* Reporting
* External integrations
* Observability
* Deployment automation

## 4.3 User Story

A User Story represents a user or stakeholder requirement that delivers measurable value.

The recommended format is:

```text
As a <user role>, I want <capability> so that <business value>.
```

A User Story should:

* Be linked to one Feature
* Be small enough to complete within a development iteration
* Include testable acceptance criteria
* Define relevant business rules and exceptions
* Reference the related PRD requirement
* Avoid unnecessary implementation details

Technical requirements that do not directly represent user behavior may be created as technical User Stories.

## 4.4 Task

A Task represents a specific implementation activity required to complete a User Story.

Tasks may include:

* Backend development
* Frontend development
* AI or agent implementation
* Infrastructure configuration
* CI/CD changes
* Database changes
* Integration development
* Automated testing
* Documentation
* Security validation

Each Task should:

* Be linked to one User Story
* Have a clear owner
* Define a concrete deliverable
* Be independently trackable
* Be small enough to complete within a short development period

## 4.5 Work-Item Traceability

Every work item must maintain traceability to the PRD.

Each Epic, Feature, and User Story should include:

* Related PRD section or requirement ID
* Description
* Acceptance criteria
* Dependencies
* Assumptions and constraints
* Relevant technical or business references

This structure ensures that every development activity can be traced back to an approved project requirement.

# 5. Development and Git Workflow

## 5.1 Task Readiness

A Task can enter development when:

* It is linked to a User Story
* Its scope is clear
* Its expected output is defined
* Acceptance criteria are available
* Dependencies are identified
* Required designs, credentials, APIs, and environments are available
* An owner is assigned

Tasks that do not meet these conditions should remain in a refinement or blocked state.

## 5.2 Branch Strategy

The `master` branch represents the stable and deployable codebase.

Developers must not commit directly to the `master` branch.

All changes must be developed in dedicated branches and merged through pull requests.

Recommended branch types are:

* `feature/`: New functionality
* `bugfix/`: Defect resolution
* `hotfix/`: Urgent production correction
* `refactor/`: Internal code improvement
* `chore/`: Maintenance, configuration, or tooling changes
* ``: Documentation changes

Branch names should include the related Azure Boards work-item ID and a short description.

Examples:

```text
feature/1234-invoice-validation
bugfix/1452-fix-token-refresh
chore/1510-update-ci-pipeline
```

Each branch should normally relate to one Task or one closely related group of Tasks.

## 5.3 Starting Development

Before creating a branch, the developer should update the local `master` branch:

```bash
git checkout master
git pull origin master
git checkout -b feature/1234-invoice-validation
```

The developer implements the change according to:

* The related Task
* User Story acceptance criteria
* PRD requirements
* Repository coding standards
* Architecture guidelines
* Security guidelines

## 5.4 Commit Guidelines

Commits should be small, focused, and understandable.

Recommended commit format:

```text
<type>: <description> AB#<work-item-id>
```

Examples:

```text
feat: add invoice validation rules AB#1234
fix: handle expired access tokens AB#1452
test: add invoice parser unit tests AB#1234
```

Common commit types include:

* `feat`
* `fix`
* `test`
* `refactor`
* `docs`
* `chore`
* `ci`

Temporary or unclear commit messages such as `update`, `changes`, or `fix stuff` should be avoided.

## 5.5 Development Requirements

Before opening a pull request, the developer must:

* Complete the required implementation
* Add or update automated tests
* Run relevant tests locally
* Apply formatting and linting rules
* Perform static code analysis where applicable
* Verify that no secrets or sensitive data are committed
* Update documentation and configuration when required
* Confirm that acceptance criteria are satisfied
* Synchronize the branch with the latest `master`

The branch should be updated using the repository's agreed merge or rebase approach.

## 5.6 Pull Request Creation

A pull request must be opened from the development branch to the `master` branch.

The pull request should include:

* A clear title
* Summary of the implemented change
* Related Azure Boards work item
* Testing performed
* Configuration or deployment impact
* Database migration impact
* Security considerations
* Screenshots or API examples when relevant
* Known limitations
* Follow-up work

Recommended pull request title format:

```text
AB#1234 Add invoice validation
```

The pull request must be linked to the relevant Azure Boards work item.

Automatic work-item completion may be enabled only when merging the pull request fully completes the related work.

## 5.7 Pull Request Validation

The pull request must pass all required quality gates before approval.

Validation may include:

* Build validation
* Unit tests
* Integration tests
* Code formatting and linting
* Static application security testing
* Dependency scanning
* Secret scanning
* SonarQube quality gate
* Artifact or container image build
* Database migration validation
* Required reviewer approval

Failed validation checks must be resolved before merging.

## 5.8 Code Review

Reviewers should evaluate:

* Compliance with the Task
* Compliance with acceptance criteria
* Code correctness
* Code readability
* Architecture and design consistency
* Test coverage
* Security risks
* Error handling
* Logging
* Performance implications
* Backward compatibility
* Deployment and operational impact

Review comments must be resolved or explicitly acknowledged before approval.

The pull request author must not be the only approver.

## 5.9 Merge Strategy

Pull requests should be merged only after:

* Required checks have passed
* Required approvals have been received
* Review comments have been resolved
* The branch is up to date with `master`
* The linked work item is ready for completion

A consistent merge strategy should be used across repositories.

Squash merge is recommended to keep the `master` branch history clean and ensure that each pull request produces one meaningful commit.

After merging:

* The source branch should be deleted
* The related Azure Boards work item should be updated
* Follow-up work should be created as separate work items
* The automated deployment process should be triggered

# 6. Automated Deployment Process

Merging a pull request into the `master` branch triggers the automated deployment process.

The automated process may include:

* Building application artifacts
* Running final validation checks
* Running security checks
* Creating versioned packages or container images
* Publishing generated artifacts
* Updating deployment configurations
* Deploying the approved version
* Running post-deployment health checks
* Recording deployment status and logs
* Sending success or failure notifications

Deployment failures must not be ignored.

The responsible team must:

* Review the automated process logs
* Identify the cause of the failure
* Correct the issue or initiate the defined rollback process
* Record any required follow-up work

Manual changes outside the automated deployment process should be avoided to maintain:

* Consistency
* Traceability
* Repeatability
* Auditability
