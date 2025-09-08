from mcp.server.fastmcp import FastMCP
from httpx import Response
import inspect



try:
    from package_info import VersionInfo
except ImportError as ie:
    PKG_INFO_MODULE_NAME = "package_info"
    import sys
    import importlib.util
    from pathlib import Path
    # Import VersionInfo using relative path
    _current_dir = Path(__file__).parent
    _package_info_path = _current_dir.parent / f"{PKG_INFO_MODULE_NAME}.py"
    _spec = importlib.util.spec_from_file_location(PKG_INFO_MODULE_NAME, _package_info_path)
    if _spec is None:
        raise ImportError(f"Could not create a module spec for {PKG_INFO_MODULE_NAME} at {_package_info_path}") from ie
    _package_info = importlib.util.module_from_spec(_spec)
    sys.modules[PKG_INFO_MODULE_NAME] = _package_info
    if _spec.loader is None:
        raise ImportError(f"Could not load {_package_info_path}") from ie
    _spec.loader.exec_module(_package_info)
    VersionInfo = _package_info.VersionInfo  # type: ignore[misc]

from statscan.wds.requests import WDSRequests
from statscan.wds.client import Client


mcp = FastMCP('statscan')

client = Client(timeout=30)

@mcp.resource('resource://codes')
async def get_codes() -> dict:
    return await client.get_code_sets()

@mcp.resource('resource://version')
def get_version() -> dict:
    vi = VersionInfo.from_version_file()
    return vi.to_dict()

@mcp.resource('wds://requests')
async def get_wds_requests() -> dict:
    # get a list of all requests, including their args and kwargs  (including their types) and return type using inspect
    requests = {}
    for name, func in inspect.getmembers(WDSRequests, inspect.isfunction):
        if inspect.signature(func).return_annotation is Response:
            meth = {}
            argspec = inspect.getfullargspec(func)
            if arg_dict := argspec._asdict():
                meth.update(arg_dict)
            if doc := inspect.getdoc(func):
                meth['doc'] = doc

            requests[name] = meth
    return requests

@mcp.tool()
async def echo(text: str) -> str:
    """
    Echoes the input text.
    """
    return text

if __name__ == "__main__":
    mcp.run()