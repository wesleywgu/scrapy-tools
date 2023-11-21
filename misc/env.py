import os


def get_env():
    env = os.environ['env']
    print("machine env={}".format(env))
    return env
