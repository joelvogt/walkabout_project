from clients.walkabout_experiment import ExperimentConsumer, FrameAction


class DoFrame(FrameAction):
    def __init__(self):
        print('init')

    def __call__(self, frame):
        print(frame)

    def close(self):
        print('bye bye')


f = ExperimentConsumer('pixelman_data', DoFrame())

f.listen()