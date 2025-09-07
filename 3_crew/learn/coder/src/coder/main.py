#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from coder.crew import Coder

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

assignment = "Write a python program to calculate the first 10,000 terms \
    of the series, multiplying the total by 4: 1 - 1/3 + 1/5 - 1/7 + 1/9 - ..."
def run():
    inputs = {
        "assignment": assignment
    }
    result = Coder().crew().kickoff(inputs=inputs)
    print(result.raw)