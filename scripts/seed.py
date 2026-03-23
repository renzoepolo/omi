from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models import FormFieldDefinition, Layer, LayerType, Project, ProjectLayer, ProjectRole, User, UserProject


def run() -> None:
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as db:
        admin = db.scalar(select(User).where(User.email == "admin@omi.local"))
        if not admin:
            admin = User(email="admin@omi.local", hashed_password=get_password_hash("admin123"))
            db.add(admin)

        renzo = db.scalar(select(User).where(User.email == "renzo@omi.local"))
        if not renzo:
            renzo = User(email="renzo@omi.local", hashed_password=get_password_hash("renzo123"))
            db.add(renzo)

        p1 = db.scalar(select(Project).where(Project.name == "Proyecto A"))
        if not p1:
            p1 = Project(name="Proyecto A")
            db.add(p1)

        p2 = db.scalar(select(Project).where(Project.name == "Proyecto B"))
        if not p2:
            p2 = Project(name="Proyecto B")
            db.add(p2)

        db.flush()

        links = {
            (admin.id, p1.id): ProjectRole.SUPER_ADMIN,
            (admin.id, p2.id): ProjectRole.PROJECT_ADMIN,
            (renzo.id, p1.id): ProjectRole.EDITOR,
        }

        for (user_id, project_id), role in links.items():
            exists = db.scalar(
                select(UserProject).where(
                    UserProject.user_id == user_id,
                    UserProject.project_id == project_id,
                )
            )
            if not exists:
                db.add(UserProject(user_id=user_id, project_id=project_id, role=role))

        base_layers = [
            ("Catastro", "omi", "catastro_base", LayerType.WMS, True, 1),
            ("Parcelas", "omi", "parcelas", LayerType.WFS, True, 10),
            ("Zonificacion", "omi", "zonificacion", LayerType.WMS, False, 20),
        ]
        for name, workspace, layer_name, layer_type, visible, z_index in base_layers:
            layer = db.scalar(select(Layer).where(Layer.name == name))
            if not layer:
                layer = Layer(
                    name=name,
                    geoserver_workspace=workspace,
                    geoserver_layer_name=layer_name,
                    type=layer_type,
                    default_visible=visible,
                    z_index=z_index,
                )
                db.add(layer)

        db.flush()

        catastro = db.scalar(select(Layer).where(Layer.name == "Catastro"))
        parcelas = db.scalar(select(Layer).where(Layer.name == "Parcelas"))
        zonificacion = db.scalar(select(Layer).where(Layer.name == "Zonificacion"))
        assert catastro and parcelas and zonificacion

        project_layer_links = [
            (p1.id, catastro.id, True, 1),
            (p1.id, parcelas.id, True, 11),
            (p2.id, catastro.id, True, 1),
            (p2.id, zonificacion.id, False, 21),
        ]
        for project_id, layer_id, visible_override, z_override in project_layer_links:
            exists = db.scalar(
                select(ProjectLayer).where(
                    ProjectLayer.project_id == project_id,
                    ProjectLayer.layer_id == layer_id,
                )
            )
            if not exists:
                db.add(
                    ProjectLayer(
                        project_id=project_id,
                        layer_id=layer_id,
                        visible_override=visible_override,
                        z_index_override=z_override,
                    )
                )

        default_form_fields = [
            ("owner_name", "Titular", "text", True, 10, {"max_length": 255}),
            ("contact_phone", "Telefono", "text", False, 20, {"max_length": 30}),
            ("inspection_notes", "Observaciones", "textarea", False, 30, {}),
        ]
        for field_key, label, field_type, required, order_index, config in default_form_fields:
            exists = db.scalar(
                select(FormFieldDefinition).where(
                    FormFieldDefinition.project_id == p1.id,
                    FormFieldDefinition.field_key == field_key,
                )
            )
            if not exists:
                db.add(
                    FormFieldDefinition(
                        project_id=p1.id,
                        field_key=field_key,
                        label=label,
                        field_type=field_type,
                        required=required,
                        order_index=order_index,
                        config=config,
                    )
                )

        db.commit()


if __name__ == "__main__":
    run()
