from rest_framework.permissions import BasePermission, SAFE_METHODS


# ===================== Role-Based Permissions ===================== #

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'manager'


class IsCashier(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'cashier'


class IsAccountant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'accountant'


class IsWarehouse(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'warehouse'


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in {
            'cashier', 'accountant', 'warehouse'
        }


# ===================== Combination Permissions ===================== #

class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in {
            'admin', 'manager'
        }


class IsAdminOrStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in {
            'admin', 'cashier', 'accountant', 'warehouse'
        }


class IsManagerOrStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in {
            'manager', 'cashier', 'accountant', 'warehouse'
        }


class SuperPermission(BasePermission):
    """Admin, Manager, or Staff can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in {
            'admin', 'manager', 'cashier', 'accountant', 'warehouse'
        }


# ===================== Read/Write Restrictions ===================== #

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and request.user.is_authenticated


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and (
                request.method in SAFE_METHODS or request.user.role == 'admin'
            )
        )


class BranchOrReadOnly(BasePermission):
    """Allow full access if in same branch, else read-only"""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == 'admin':
            return True
        user_branch = getattr(request.user, 'branch', None)
        obj_branch = getattr(obj, 'branch', None)
        return user_branch and obj_branch and user_branch.id == obj_branch.id


class OwnerOrReadOnly(BasePermission):
    """Only the creator can edit/delete, others can only view"""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return hasattr(obj, 'created_by') and obj.created_by == request.user


class IsSelfOrAdmin(BasePermission):
    """Users can edit their own profile, or admin can edit anyone's"""
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated and (
                obj == request.user or request.user.role == 'admin'
            )
        )


# ===================== Object-Level Branch & Creator ===================== #

class BranchRestrictedAccess(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        user_branch = request.user.branch
        obj_branch = getattr(obj, 'branch', None)
        if obj_branch and user_branch:
            return obj_branch.id == user_branch.id
        if hasattr(obj, 'sale') and obj.sale.branch and user_branch:
            return obj.sale.branch.id == user_branch.id
        return False


class CreatorOrAdminAccess(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False
