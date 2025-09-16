"""
自定义异常类模块
定义系统中使用的各种异常类型
"""


class CoreReflowError(Exception):
    """基础异常类"""
    pass


class ConfigurationError(CoreReflowError):
    """配置相关错误"""
    pass


class GitLabAPIError(CoreReflowError):
    """GitLab API调用错误"""
    def __init__(self, message: str, status_code: int = None, response_data: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class GitOperationError(CoreReflowError):
    """Git操作相关错误"""
    pass


class FingerprintGenerationError(CoreReflowError):
    """指纹生成错误"""
    pass


class ValidationError(CoreReflowError):
    """验证相关错误"""
    pass


class NetworkTimeoutError(CoreReflowError):
    """网络超时错误"""
    pass


class RepositoryAccessError(GitOperationError):
    """仓库访问权限错误"""
    pass


class BranchNotFoundError(GitOperationError):
    """分支不存在错误"""
    def __init__(self, branch_name: str):
        self.branch_name = branch_name
        super().__init__(f"Branch '{branch_name}' not found")


class MRNotFoundError(GitLabAPIError):
    """MR不存在错误"""
    def __init__(self, mr_id: int):
        self.mr_id = mr_id
        super().__init__(f"MR #{mr_id} not found")


class InvalidInputError(ValidationError):
    """无效输入错误"""
    pass
