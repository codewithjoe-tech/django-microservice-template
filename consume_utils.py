import logging
from app.models import UserCache as Users, Tenants, TenantUsers , Community , CommunityMembers

logger = logging.getLogger(__name__)

def user_callback(ch, event_type, data, method):
    try:
        user_id = data.get('id')
        if not user_id:
            logger.error(f"Missing user ID in event: {data}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        if event_type == 'created':
            Users.objects.create(
                username=data['username'],
                id=user_id,
                profile_pic=data.get('profile_pic', ''),
                full_name=data['full_name'],
                is_superuser=data['is_superuser']
            )
            logger.info(f"Created user: {data}")

        elif event_type == 'updated':
            try:
                user = Users.objects.get(id=user_id)
                for key, value in data.items():
                    if hasattr(user, key) and value is not None:
                        setattr(user, key, value)
                user.save()
                logger.info(f"Updated user with ID: {user_id}")
            except Users.DoesNotExist:
                logger.error(f"User with ID {user_id} not found for update")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

        elif event_type == 'deleted':
            deleted_count, _ = Users.objects.filter(id=user_id).delete()
            if deleted_count > 0:
                logger.info(f"Deleted user with ID: {user_id}")
            else:
                logger.warning(f"User with ID {user_id} not found for deletion")

        else:
            logger.warning(f"Unknown user event type: {event_type}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing user event: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def tenant_callback(ch, event_type, data, method):
    try:
        tenant_id = data.get('id')
        if not tenant_id:
            logger.error(f"Missing tenant ID in event: {data}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        if event_type == 'created':
            tenant = Tenants.objects.create(
                name=data['name'],
                subscription_plan=data['subscription_plan'],
                subdomain=data['subdomain'],
                id=tenant_id
            )
            try:
                admin = Users.objects.get(id=data['admin'])
                TenantUsers.objects.create(tenant=tenant, user=admin, is_admin=True)
            except Users.DoesNotExist:
                logger.warning(f"Admin user with ID {data['admin']} not found for tenant {tenant_id}")

            logger.info(f"Created tenant: {data}")

        elif event_type == 'updated':
            try:
                tenant = Tenants.objects.get(id=tenant_id)
                for key, value in data.items():
                    if hasattr(tenant, key) and value is not None:
                        setattr(tenant, key, value)
                tenant.save()
                logger.info(f"Updated tenant with ID: {tenant_id}")
            except Tenants.DoesNotExist:
                logger.error(f"Tenant with ID {tenant_id} not found for update")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

        elif event_type == 'deleted':
            deleted_count, _ = Tenants.objects.filter(id=tenant_id).delete()
            if deleted_count > 0:
                logger.info(f"Deleted tenant with ID: {tenant_id}")
            else:
                logger.warning(f"Tenant with ID {tenant_id} not found for deletion")

        else:
            logger.warning(f"Unknown tenant event type: {event_type}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing tenant event: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def tenantuser_callback(ch, event_type, data, method):
    try:
        tenant_user_id = data.get('id')
        if not tenant_user_id:
            logger.error(f"Missing tenant-user ID in event: {data}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        if event_type == 'created':
            try:
                tenant = Tenants.objects.get(id=data['tenant'])
                user = Users.objects.get(id=data['user'])
                
                # Check if the user-tenant association already exists
                existing_association = TenantUsers.objects.filter(tenant=tenant, user=user).exists()
                if not existing_association:
                    TenantUsers.objects.create(tenant=tenant, user=user, is_admin=data.get('is_admin', False))
                    logger.info(f"Created tenant-user association: {data}")
                else:
                    logger.info(f"Tenant-user association already exists for user {data['user']} in tenant {data['tenant']}")

            except (Tenants.DoesNotExist, Users.DoesNotExist) as e:
                logger.error(f"Error creating tenant-user association: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

        elif event_type == 'updated':
            try:
                tenant_user = TenantUsers.objects.get(id=tenant_user_id)
                for key, value in data.items():
                    if hasattr(tenant_user, key) and value is not None and key not in ('tenant', 'user'):
                        setattr(tenant_user, key, value)
                tenant_user.save()
                logger.info(f"Updated tenant-user with ID: {tenant_user_id}")
            except TenantUsers.DoesNotExist:
                logger.error(f"TenantUser with ID {tenant_user_id} not found for update")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

        elif event_type == 'deleted':
            deleted_count, _ = TenantUsers.objects.filter(id=tenant_user_id).delete()
            if deleted_count > 0:
                logger.info(f"Deleted tenant-user with ID: {tenant_user_id}")
            else:
                logger.warning(f"TenantUser with ID {tenant_user_id} not found for deletion")

        else:
            logger.warning(f"Unknown tenant-user event type: {event_type}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing tenant-user event: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)



def community_callback(ch, event_type, data, method):
    try:
        if event_type == "created":
            try:
                tenant = Tenants.objects.get(id=data['tenant'])

                Community.objects.create(
                    id = data['id'],
                    name = data['title'],
                    tenant = tenant

                )
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing course event: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        elif event_type == "updated":
            try:
                Community.objects.filter(id = data['id']).update(name=data['title'])
                # CourseCache.objects.filter(id = data['id']).update(price=data['price'])
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing course event: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        elif event_type == "deleted":
            try:
                # CourseCache.objects.filter(id = data['id']).delete()
                Community.objects.filter(id = data['id']).delete()
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing course event: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        

    except Exception as e:
        logger.error(f"Error processing course event: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)



def order_callback(ch, event_type, data, method):
    try:
        tenantuser = TenantUsers.objects.get(id=data['user'])
        tenant = tenantuser.tenant
        community = Community.objects.get(id=data['course'])

        if event_type == 'created':
            CommunityMembers.objects.create(
                user=tenantuser,
                community=community,
                tenant=tenant
            )
            logger.info(f"Created order: {data}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    except TenantUsers.DoesNotExist:
        logger.error(f"Tenant user with ID {data['user']} not found")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Community.DoesNotExist:
        logger.error(f"Course with ID {data['course']} not found")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    except Exception as e:
        logger.error(f"Error processing order event: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
