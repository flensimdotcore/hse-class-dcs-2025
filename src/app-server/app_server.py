from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
from sqlalchemy import create_engine, text, Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

class ProcessRequest(BaseModel):
    number: int

class ProcessResponse(BaseModel):
    result: int
    processed_number: int

class ErrorResponse(BaseModel):
    error: str
    code: str

app = FastAPI(title="Application Server", version="1.0.0")

class Database:
    def __init__(self):
        self.dsn = DATABASE_URL
        self.engine = None
        self.SessionLocal = None

    def connect(self):
        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to database (attempt {attempt + 1})")
                self.engine = create_engine(self.dsn, pool_pre_ping=True)
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Successfully connected to database: {self.dsn}")
                return
            except Exception as e:
                logger.error(f"Database connection failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e

    def check_number_exists(self, number: int) -> bool:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM processed_numbers WHERE number = :number"),
                    {"number": number}
                )
                exists = result.fetchone() is not None
                logger.info(f"Number {number} exists: {exists}")
                return exists
        except Exception as e:
            logger.error(f"Error checking number existence: {e}")
            raise

    def get_last_number(self) -> int:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT number FROM processed_numbers ORDER BY number DESC LIMIT 1")
                )
                row = result.fetchone()
                last_num = row[0] if row else -1
                logger.info(f"Last processed number: {last_num}")
                return last_num
        except Exception as e:
            logger.error(f"Error getting last number: {e}")
            return -1

    def insert_number(self, number: int) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO processed_numbers (number) VALUES (:number)"),
                    {"number": number}
                )
                conn.commit()
            logger.info(f"Successfully inserted number: {number}")
            return True
        except Exception as e:
            logger.error(f"Database insert error for number {number}: {e}")
            return False

    def get_all_numbers(self):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT number FROM processed_numbers ORDER BY number"))
                numbers = [row[0] for row in result.fetchall()]
                return numbers
        except Exception as e:
            logger.error(f"Error getting all numbers: {e}")
            raise

db = Database()

@app.on_event("startup")
def startup_event():
    try:
        db.connect()
        logger.info("Application server started successfully")
    except Exception as e:
        logger.error(f"Failed to start application server: {e}")
        raise

@app.post("/process", response_model=ProcessResponse, responses={
    400: {"model": ErrorResponse},
    409: {"model": ErrorResponse}
})
async def process_number(request: ProcessRequest):
    try:
        logger.info(f"Processing number: {request.number}")
        number = request.number

        if number < 0:
            error_msg = "Number must be non-negative"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail={"error": error_msg, "code": "INVALID_NUMBER"})

        if db.check_number_exists(number):
            error_msg = f"Duplicate number: {number}"
            logger.error(error_msg)
            raise HTTPException(status_code=409, detail={"error": error_msg, "code": "DUPLICATE_NUMBER"})

        last_number = db.get_last_number()
        logger.info(f"Last number: {last_number}, current number: {number}")

        if last_number != -1 and number != last_number + 1:
            error_msg = f"Sequence violation: received {number}, expected {last_number + 1}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail={"error": error_msg, "code": "SEQUENCE_VIOLATION"})

        if db.insert_number(number):
            result = number + 1
            logger.info(f"Successfully processed number {number}, result: {result}")
            return ProcessResponse(result=result, processed_number=number)
        else:
            error_msg = f"Failed to save number: {number}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail={"error": error_msg, "code": "SAVE_ERROR"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in process_number: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "code": "UNEXPECTED_ERROR"})

@app.get("/health")
async def health_check():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "application-server", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "service": "application-server", "database": "disconnected"}, 503

@app.get("/numbers")
async def get_processed_numbers():
    try:
        numbers = db.get_all_numbers()
        return {"processed_numbers": numbers}
    except Exception as e:
        logger.error(f"Error getting numbers: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to retrieve numbers"})

@app.get("/")
async def root():
    return {"message": "Application Server is running", "version": "1.0.0"}
