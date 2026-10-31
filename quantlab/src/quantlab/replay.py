"""Bar replay. The full series is private; every public method exposes only bars up to the cursor,
so the future can never leak into a chart, an indicator or a screenshot."""
from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from .charts import candlestick


class Replay:
    def __init__(self, df: pd.DataFrame, start=None, window: int = 120, trades: pd.DataFrame | None = None, signals: list[dict] | None = None):
        self._df = df.reset_index(drop=True)
        self.window = window
        self._trades = trades.reset_index(drop=True) if trades is not None else None
        self._signals = signals or []          # dicts: time (bar time the signal is known), price, label
        self.cursor = 0 if start is None else int(self._df["time"].searchsorted(pd.Timestamp(start)))
        self.cursor = min(max(self.cursor, 0), len(self._df) - 1)
        self.playing = False
        self.speed = 1                          # bars per step

    # --- navigation (the only way the cursor moves)
    def step(self, n: int | None = None) -> int:
        self.cursor = min(self.cursor + (n or self.speed), len(self._df) - 1)
        return self.cursor

    def back(self, n: int = 1) -> int:
        self.cursor = max(self.cursor - n, 0)
        return self.cursor

    def jump_to(self, ts) -> int:
        self.cursor = min(int(self._df["time"].searchsorted(pd.Timestamp(ts))), len(self._df) - 1)
        return self.cursor

    def set_speed(self, bars_per_step: int) -> None:
        self.speed = max(int(bars_per_step), 1)

    def pause(self) -> None:
        self.playing = False

    def resume(self) -> None:
        self.playing = True

    @property
    def now(self) -> pd.Timestamp:
        return pd.Timestamp(self._df["time"].iloc[self.cursor])

    @property
    def at_end(self) -> bool:
        return self.cursor >= len(self._df) - 1

    # --- the only data accessors
    def visible(self) -> pd.DataFrame:
        return self._df.iloc[: self.cursor + 1].copy()

    def visible_window(self) -> pd.DataFrame:
        return self._df.iloc[max(self.cursor + 1 - self.window, 0): self.cursor + 1].copy()

    def _overlays(self, view: pd.DataFrame):
        markers, lines = [], []
        t0 = view["time"].iloc[0]
        for s in self._signals:
            if t0 <= pd.Timestamp(s["time"]) <= self.now:
                markers.append({"time": s["time"], "price": s["price"], "kind": "signal", "label": s.get("label", "")})
        if self._trades is not None:
            for r in self._trades.itertuples():
                if r.entry_time > self.now:
                    continue
                if r.entry_time >= t0:
                    markers.append({"time": r.entry_time, "price": r.entry_fill, "kind": "entry_long" if r.side == 1 else "entry_short", "label": "entry"})
                if r.exit_time <= self.now:
                    if r.exit_time >= t0:
                        markers.append({"time": r.exit_time, "price": r.exit_fill, "kind": "exit", "label": f"{r.net_R:+.2f}R"})
                else:  # position still open at the cursor: show its stop/target, never the exit
                    lines.append({"price": r.stop, "label": "stop", "color": "#c22"})
                    if r.tp is not None and not pd.isna(r.tp):
                        lines.append({"price": r.tp, "label": "target", "color": "#0a7"})
        return markers, lines

    def render(self, path=None, title: str | None = None):
        view = self.visible_window()
        markers, lines = self._overlays(view)
        return candlestick(view, path, title or f"{self.now}", markers=markers, hlines=lines)

    def export_video(self, path, n_frames: int = 120, fps: int = 8, stride: int | None = None) -> str:
        """GIF (always) or MP4 (when path ends with .mp4 and ffmpeg exists). Frames use only bars up to each cursor."""
        import matplotlib.pyplot as plt
        from PIL import Image
        stride = stride or self.speed
        start_cursor = self.cursor
        frames = []
        for _ in range(n_frames):
            fig = self.render()
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=70)
            plt.close(fig)
            buf.seek(0)
            frames.append(Image.open(buf).convert("RGB"))
            if self.at_end:
                break
            self.step(stride)
        self.cursor = start_cursor
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".mp4" and shutil.which("ffmpeg"):
            with tempfile.TemporaryDirectory() as td:
                for k, im in enumerate(frames):
                    im.save(Path(td) / f"f{k:05d}.png")
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(Path(td) / "f%05d.png"),
                                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p", str(path)], check=True)
            return str(path)
        gif = path.with_suffix(".gif")
        frames[0].save(gif, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
        return str(gif)
