from threading import Timer
from typing import Union

cooldowns = []


def end_cooldown(func):
    cooldowns.remove(func)


def start_cooldown(func, interval: Union[int, float]):
    cooldowns.append(func)
    print(cooldowns)
    Timer(interval, end_cooldown, [func]).start()


def cooldown(interval):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if func in cooldowns:
                return
            func(*args, **kwargs)
            start_cooldown(func, interval)

        return wrapper

    return decorator


@cooldown(30.0)
def obamna():
    print("Hello, world!")


if __name__ == "__main__":
    while True:
        input("Press any key to run obamna")
        obamna()
