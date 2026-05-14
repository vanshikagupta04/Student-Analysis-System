```python
virtual environemnt =  python -m venv venv
activation = venv\Scripts\activate
backend = uvicorn backend.main:app --reload
frontend = streamlit run frontend/app.py
```