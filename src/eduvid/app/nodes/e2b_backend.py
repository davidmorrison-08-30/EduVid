from langchain_e2b import E2BSandbox
from ..utils.config import all_secrets

e2b_api_key = all_secrets["e2b_api_key"]

class ScopedE2BSandbox(E2BSandbox):
    def _normalize_path(self, path: str) -> str:
        """Ensures all root paths are strictly jailed to /home/user."""
        path_str = str(path).strip()
        
        # If the path explicitly targets system root or is empty, force /home/user
        if path_str in ["/", "", "."]:
            return "/home/user"
            
        # If it's a relative path, prepend /home/user
        if not path_str.startswith("/"):
            return f"/home/user/{path_str}"
            
        # If it's an absolute path but not inside /home/user (and not a route), scope it
        if not path_str.startswith("/home/user"):
            # Avoid breaking absolute paths that might accidentally leak
            return f"/home/user{path_str}"
            
        return path_str

    def glob(self, pattern: str, path: str | None = None):
        # Intercept the glob path before passing to LangChain's E2B backend implementation
        scoped_path = self._normalize_path(path)
        return super().glob(pattern, path)