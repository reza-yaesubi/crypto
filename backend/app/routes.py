"""REST API routes for portfolio and watchlist."""

from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from app import database, portfolio, watchlist

router = APIRouter()


def get_conn():
    conn = database.connect()
    try:
        yield conn
    finally:
        conn.close()


def get_cache(request: Request):
    return request.app.state.price_cache


class TradeRequest(BaseModel):
    pair: str
    quantity: float
    side: Literal["buy", "sell"]


class WatchlistRequest(BaseModel):
    pair: str


@router.get("/api/portfolio")
def read_portfolio(conn=Depends(get_conn), cache=Depends(get_cache)) -> dict:
    return portfolio.get_portfolio(conn, cache)


@router.post("/api/portfolio/trade")
def post_trade(req: TradeRequest, conn=Depends(get_conn), cache=Depends(get_cache)):
    try:
        return portfolio.execute_trade(conn, cache, req.pair, req.side, req.quantity)
    except portfolio.TradeError as exc:
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})


@router.get("/api/portfolio/history")
def read_history(conn=Depends(get_conn)) -> list[dict]:
    return portfolio.get_history(conn)


@router.get("/api/watchlist")
def read_watchlist(conn=Depends(get_conn)) -> list[dict]:
    return watchlist.list_watchlist(conn)


@router.post("/api/watchlist", status_code=201)
def post_watchlist(req: WatchlistRequest, conn=Depends(get_conn)):
    try:
        return watchlist.add_watchlist(conn, req.pair)
    except watchlist.WatchlistError as exc:
        return JSONResponse(status_code=409, content={"error": str(exc)})


@router.delete("/api/watchlist/{pair}", status_code=204)
def delete_watchlist(pair: str, conn=Depends(get_conn)) -> Response:
    watchlist.remove_watchlist(conn, pair)
    return Response(status_code=204)
