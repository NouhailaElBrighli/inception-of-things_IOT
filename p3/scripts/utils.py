import shutil
import subprocess
import time
from datetime import timedelta


def colpr(color: str, *args: str, end: str = "\n") -> None:
    """
    Prints colored text.

    Args:
        color (str): The color of the text [r, g, v, b, y, c, w, m, k, d, u].
        args (str): The text to be printed.
        end (str): The end character.

    Returns:
        None
    """

    colors = {
        "r": "\033[91m",
        "g": "\033[92m",
        "v": "\033[95m",
        "b": "\033[94m",
        "y": "\033[93m",
        "c": "\033[96m",
        "w": "\033[97m",
        "m": "\033[95m",
        "k": "\033[90m",
        "d": "\033[2m",
        "u": "\033[4m",
    }
    print(colors[color] + "".join(args) + "\033[0m", flush=True, end=end)


def elapsed_time(start: float) -> str:
    """
    Format the elapsed time from the start time to the current time.

    Args:
        start (float): The start time in seconds.

    Returns:
        str: The formatted elapsed time.
    """

    elapsed_time = time.time() - start
    delta = timedelta(seconds=elapsed_time)

    weeks = delta.days // 7
    days = delta.days % 7
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = delta.microseconds // 1000

    if weeks > 0:
        return f"{weeks}w {days}d {hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif days > 0:
        return f"{days}d {hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif hours > 0:
        return f"{hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif minutes > 0:
        return f"{minutes}min {seconds}s {milliseconds}ms"
    elif seconds > 0:
        return f"{seconds}s {milliseconds}ms"
    else:
        return f"{milliseconds}ms"


def command_exists(cmd):
    return shutil.which(cmd) is not None


def run(cmd, capture_output=False):
    print(f"Running: {cmd}")
    if capture_output:
        result = subprocess.run(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result
    else:
        return subprocess.run(cmd, shell=True)
