FROM python:3.12-alpine
WORKDIR /app
COPY solution.py .
ENV TEST_INPUTS_PATH=/workspace/test_inputs.json
ENV RESULTS_PATH=/workspace/results.json
CMD ["python", "solution.py"]
