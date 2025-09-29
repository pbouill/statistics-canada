from mcp.server.fastmcp import FastMCP
from httpx import Response
import inspect

import statscan
from statscan.wds.requests import WDSRequests
from statscan.wds.client import Client


mcp = FastMCP("statscan")

client = Client(timeout=30)


@mcp.resource("resource://codes")
async def get_codes() -> dict:
    resp = await WDSRequests.get_code_sets(client=client)
    resp.raise_for_status()
    return resp.json()


@mcp.resource("resource://version")
def get_version() -> str:
    return statscan.__version__


@mcp.resource("wds://requests")
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
                meth["doc"] = doc

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
