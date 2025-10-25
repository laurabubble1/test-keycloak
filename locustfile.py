from locust import HttpUser, task, between
import requests
import time
import uuid
import random
import json


class KeycloakUser(HttpUser):
    wait_time = between(2, 5)  # Think time between requests (2-5 seconds)
    host = "http://host.docker.internal:8080"
    
    def on_start(self):
        """Initialize user session with admin token"""
        self.token_expires_at = 0
        self.test_realm_name = f"test-realm-{uuid.uuid4().hex[:8]}"
        self.created_resources = {
            'users': [],
            'clients': [],
            'realms': [],
            'roles': [],
            'groups': []
        }
        self.get_admin_token()
        # Create a test realm for isolated testing
        self.create_test_realm()
    
    def on_stop(self):
        """Cleanup resources when user session ends"""
        self.cleanup_resources()
    
    def get_admin_token(self):
        """Get admin access token for Keycloak admin API"""
        token_url = f"{self.host}/realms/master/protocol/openid-connect/token"
        token_data = {
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin"
        }
        
        response = self.client.post(token_url, data=token_data, name="auth/get_admin_token")
        if response.status_code == 200:
            token_info = response.json()
            self.admin_token = token_info["access_token"]
            self.token_expires_at = time.time() + (token_info.get("expires_in", 300) - 60)
            self.client.headers.update({"Authorization": f"Bearer {self.admin_token}"})
        else:
            print(f"Failed to get admin token: {response.status_code}")
    
    def ensure_valid_token(self):
        """Refresh token if needed"""
        if time.time() >= self.token_expires_at:
            self.get_admin_token()
    
    def create_test_realm(self):
        """Create a test realm for isolated testing"""
        realm_data = {
            "realm": self.test_realm_name,
            "displayName": f"Test Realm {self.test_realm_name}",
            "enabled": True
        }
        response = self.client.post("/admin/realms", json=realm_data, name="setup/create_test_realm")
        if response.status_code == 201:
            self.created_resources['realms'].append(self.test_realm_name)

    def cleanup_resources(self):
        """Clean up created resources"""
        self.ensure_valid_token()
        # Delete test realm (this will cascade delete most resources)
        if self.test_realm_name in self.created_resources['realms']:
            self.client.delete(f"/admin/realms/{self.test_realm_name}", name="cleanup/delete_test_realm")

    # ============ CREATE OPERATIONS (5 endpoints) ============
    
    @task(2)
    def create_user(self):
        """Create a new user"""
        self.ensure_valid_token()
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"testuser_{unique_id}",
            "enabled": True,
            "firstName": f"Test_{unique_id}",
            "lastName": "User",
            "email": f"testuser_{unique_id}@example.com",
            "credentials": [{
                "type": "password",
                "value": "password123",
                "temporary": False
            }]
        }
        response = self.client.post(f"/admin/realms/{self.test_realm_name}/users", 
                                  json=user_data, name="create/user")
        if response.status_code == 201:
            # Extract user ID from location header
            location = response.headers.get('Location', '')
            if location:
                user_id = location.split('/')[-1]
                self.created_resources['users'].append(user_id)

    @task(1)
    def create_client(self):
        """Create a new client"""
        self.ensure_valid_token()
        unique_id = uuid.uuid4().hex[:8]
        client_data = {
            "clientId": f"test-client-{unique_id}",
            "name": f"Test Client {unique_id}",
            "description": "Load test client",
            "enabled": True,
            "protocol": "openid-connect",
            "publicClient": False,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True
        }
        response = self.client.post(f"/admin/realms/{self.test_realm_name}/clients", 
                                  json=client_data, name="create/client")
        if response.status_code == 201:
            location = response.headers.get('Location', '')
            if location:
                client_id = location.split('/')[-1]
                self.created_resources['clients'].append(client_id)

    @task(1)
    def create_realm_role(self):
        """Create a new realm role"""
        self.ensure_valid_token()
        unique_id = uuid.uuid4().hex[:8]
        role_data = {
            "name": f"test-role-{unique_id}",
            "description": f"Test role for load testing - {unique_id}",
            "composite": False
        }
        response = self.client.post(f"/admin/realms/{self.test_realm_name}/roles", 
                                  json=role_data, name="create/realm_role")
        if response.status_code == 201:
            self.created_resources['roles'].append(role_data['name'])

    @task(1)
    def create_group(self):
        """Create a new group"""
        self.ensure_valid_token()
        unique_id = uuid.uuid4().hex[:8]
        group_data = {
            "name": f"test-group-{unique_id}",
            "attributes": {"description": [f"Load test group {unique_id}"]}
        }
        response = self.client.post(f"/admin/realms/{self.test_realm_name}/groups", 
                                  json=group_data, name="create/group")
        if response.status_code == 201:
            location = response.headers.get('Location', '')
            if location:
                group_id = location.split('/')[-1]
                self.created_resources['groups'].append(group_id)

    @task(1)
    def create_client_scope(self):
        """Create a new client scope"""
        self.ensure_valid_token()
        unique_id = uuid.uuid4().hex[:8]
        scope_data = {
            "name": f"test-scope-{unique_id}",
            "description": f"Test client scope {unique_id}",
            "protocol": "openid-connect",
            "attributes": {"include.in.token.scope": "true"}
        }
        self.client.post(f"/admin/realms/{self.test_realm_name}/client-scopes", 
                        json=scope_data, name="create/client_scope")

    # ============ READ OPERATIONS (5 endpoints) ============
    
    @task(5)
    def read_users(self):
        """Get list of users"""
        self.ensure_valid_token()
        params = {"max": 20, "first": 0}
        self.client.get(f"/admin/realms/{self.test_realm_name}/users", 
                       params=params, name="read/users")

    @task(3)
    def read_clients(self):
        """Get list of clients"""
        self.ensure_valid_token()
        self.client.get(f"/admin/realms/{self.test_realm_name}/clients", 
                       name="read/clients")

    @task(2)
    def read_realm_roles(self):
        """Get list of realm roles"""
        self.ensure_valid_token()
        self.client.get(f"/admin/realms/{self.test_realm_name}/roles", 
                       name="read/realm_roles")

    @task(2)
    def read_groups(self):
        """Get list of groups"""
        self.ensure_valid_token()
        self.client.get(f"/admin/realms/{self.test_realm_name}/groups", 
                       name="read/groups")

    @task(4)
    def read_realm_info(self):
        """Get realm information"""
        self.ensure_valid_token()
        self.client.get(f"/admin/realms/{self.test_realm_name}", 
                       name="read/realm_info")

    # ============ UPDATE OPERATIONS (5 endpoints) ============
    
    @task(2)
    def update_user(self):
        """Update user information"""
        self.ensure_valid_token()
        if self.created_resources['users']:
            user_id = random.choice(self.created_resources['users'])
            update_data = {
                "firstName": f"Updated_{uuid.uuid4().hex[:4]}",
                "attributes": {"lastUpdated": [str(int(time.time()))]}
            }
            self.client.put(f"/admin/realms/{self.test_realm_name}/users/{user_id}", 
                           json=update_data, name="update/user")

    @task(1)
    def update_client(self):
        """Update client configuration"""
        self.ensure_valid_token()
        if self.created_resources['clients']:
            client_id = random.choice(self.created_resources['clients'])
            update_data = {
                "description": f"Updated client description - {int(time.time())}",
                "attributes": {"lastModified": str(int(time.time()))}
            }
            self.client.put(f"/admin/realms/{self.test_realm_name}/clients/{client_id}", 
                           json=update_data, name="update/client")

    @task(1)
    def update_realm_role(self):
        """Update realm role"""
        self.ensure_valid_token()
        if self.created_resources['roles']:
            role_name = random.choice(self.created_resources['roles'])
            # First get the current role to preserve existing data
            get_response = self.client.get(f"/admin/realms/{self.test_realm_name}/roles/{role_name}", 
                                         name="get/realm_role_for_update")
            if get_response.status_code == 200:
                current_role = get_response.json()
                # Update only the description while preserving other fields
                current_role["description"] = f"Updated role description - {int(time.time())}"
                self.client.put(f"/admin/realms/{self.test_realm_name}/roles/{role_name}", 
                               json=current_role, name="update/realm_role")

    @task(1)
    def update_group(self):
        """Update group information"""
        self.ensure_valid_token()
        if self.created_resources['groups']:
            group_id = random.choice(self.created_resources['groups'])
            # First get the current group to preserve existing data
            get_response = self.client.get(f"/admin/realms/{self.test_realm_name}/groups/{group_id}", 
                                         name="get/group_for_update")
            if get_response.status_code == 200:
                current_group = get_response.json()
                # Update attributes while preserving name and other required fields
                if "attributes" not in current_group:
                    current_group["attributes"] = {}
                current_group["attributes"]["description"] = [f"Updated group - {int(time.time())}"]
                current_group["attributes"]["lastModified"] = [str(int(time.time()))]
                self.client.put(f"/admin/realms/{self.test_realm_name}/groups/{group_id}", 
                               json=current_group, name="update/group")

    @task(1)
    def update_realm_settings(self):
        """Update realm settings"""
        self.ensure_valid_token()
        update_data = {
            "displayName": f"Updated Test Realm - {int(time.time())}",
            "attributes": {"lastUpdated": str(int(time.time()))}
        }
        self.client.put(f"/admin/realms/{self.test_realm_name}", 
                       json=update_data, name="update/realm_settings")

    # ============ DELETE OPERATIONS (5 endpoints) ============
    
    @task(1)
    def delete_user(self):
        """Delete a user"""
        self.ensure_valid_token()
        if len(self.created_resources['users']) > 1:  # Keep at least one user
            user_id = self.created_resources['users'].pop()
            self.client.delete(f"/admin/realms/{self.test_realm_name}/users/{user_id}", 
                              name="delete/user")

    @task(1)
    def delete_client(self):
        """Delete a client"""
        self.ensure_valid_token()
        if len(self.created_resources['clients']) > 1:  # Keep at least one client
            client_id = self.created_resources['clients'].pop()
            self.client.delete(f"/admin/realms/{self.test_realm_name}/clients/{client_id}", 
                              name="delete/client")

    @task(1)
    def delete_realm_role(self):
        """Delete a realm role"""
        self.ensure_valid_token()
        if len(self.created_resources['roles']) > 1:  # Keep at least one role
            role_name = self.created_resources['roles'].pop()
            self.client.delete(f"/admin/realms/{self.test_realm_name}/roles/{role_name}", 
                              name="delete/realm_role")

    @task(1)
    def delete_group(self):
        """Delete a group"""
        self.ensure_valid_token()
        if len(self.created_resources['groups']) > 1:  # Keep at least one group
            group_id = self.created_resources['groups'].pop()
            self.client.delete(f"/admin/realms/{self.test_realm_name}/groups/{group_id}", 
                              name="delete/group")

    @task(1)
    def delete_client_scope(self):
        """Delete a client scope (get list first, then delete)"""
        self.ensure_valid_token()
        response = self.client.get(f"/admin/realms/{self.test_realm_name}/client-scopes", 
                                 name="get_scopes_for_delete")
        if response.status_code == 200:
            scopes = response.json()
            # Find test scopes we created
            test_scopes = [s for s in scopes if s.get('name', '').startswith('test-scope-')]
            if test_scopes:
                scope_id = random.choice(test_scopes)['id']
                self.client.delete(f"/admin/realms/{self.test_realm_name}/client-scopes/{scope_id}", 
                                  name="delete/client_scope")