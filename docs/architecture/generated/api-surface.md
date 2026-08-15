<!-- GENERADO POR scripts/build_repo_graph.py — NO EDITAR A MANO -->

# Superficie de API

Endpoints extraídos de los decoradores FastAPI. El prefijo de cada router
ya viene aplicado.

## `app/api/routes/admin.py`

| Método | Ruta | Handler |
| --- | --- | --- |
| `GET` | `/admin/audit` | `admin_list_audit_logs` |
| `GET` | `/admin/geoserver/workspaces` | `admin_geoserver_workspaces` |
| `GET` | `/admin/geoserver/workspaces/{workspace}/layers` | `admin_geoserver_workspace_layers` |
| `GET` | `/admin/geoserver/workspaces/{workspace}/layers/{layer_name}/styles` | `admin_geoserver_layer_styles` |
| `GET` | `/admin/geoserver/workspaces/{workspace}/styles` | `admin_geoserver_workspace_styles` |
| `GET` | `/admin/layers` | `admin_list_layers` |
| `POST` | `/admin/layers` | `admin_create_layer` |
| `DELETE` | `/admin/layers/{layer_id}` | `admin_delete_layer` |
| `PUT` | `/admin/layers/{layer_id}` | `admin_update_layer` |
| `GET` | `/admin/projects` | `admin_list_projects` |
| `POST` | `/admin/projects` | `admin_create_project` |
| `DELETE` | `/admin/projects/{project_id}` | `admin_delete_project` |
| `PUT` | `/admin/projects/{project_id}` | `admin_update_project` |
| `PUT` | `/admin/projects/{project_id}/form-fields` | `admin_replace_project_form_configuration` |
| `POST` | `/admin/projects/{project_id}/layers` | `admin_attach_layer_to_project` |
| `DELETE` | `/admin/projects/{project_id}/layers/{layer_id}` | `admin_detach_layer_from_project` |
| `GET` | `/admin/users` | `admin_list_users` |
| `POST` | `/admin/users` | `admin_create_user` |
| `DELETE` | `/admin/users/{user_id}` | `admin_delete_user` |
| `PUT` | `/admin/users/{user_id}` | `admin_update_user` |
| `POST` | `/admin/users/{user_id}/projects` | `admin_assign_user_to_project` |
| `DELETE` | `/admin/users/{user_id}/projects/{project_id}` | `admin_unassign_user_from_project` |

## `app/api/routes/auth.py`

| Método | Ruta | Handler |
| --- | --- | --- |
| `POST` | `/auth/login` | `login` |

## `app/api/routes/observations.py`

| Método | Ruta | Handler |
| --- | --- | --- |
| `GET` | `/projects/{project_id}/observations` | `list_observations` |
| `POST` | `/projects/{project_id}/observations` | `create_observation` |
| `DELETE` | `/projects/{project_id}/observations/{observation_id}` | `delete_observation` |
| `PATCH` | `/projects/{project_id}/observations/{observation_id}` | `update_observation` |

## `app/api/routes/projects.py`

| Método | Ruta | Handler |
| --- | --- | --- |
| `GET` | `/projects` | `list_projects` |
| `GET` | `/projects/current` | `current_project_context` |

## `app/main.py`

| Método | Ruta | Handler |
| --- | --- | --- |
| `GET` | `/health` | `health` |

## `backend/app/main.py`

| Método | Ruta | Handler |
| --- | --- | --- |
| `GET` | `/health` | `health` |
| `GET` | `/projects` | `list_projects` |
| `POST` | `/projects` | `create_project` |
| `GET` | `/projects/{project_id}/base-layers` | `list_project_base_layers` |
| `POST` | `/projects/{project_id}/base-layers` | `register_base_layer` |
| `POST` | `/properties` | `create_property` |
