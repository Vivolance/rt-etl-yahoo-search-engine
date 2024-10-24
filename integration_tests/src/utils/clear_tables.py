from sqlalchemy import TextClause, text

from integration_tests.src.utils.engine import engine


class ClearTables:
    @staticmethod
    async def clear_jobs_table() -> None:
        """
        Runs at the start of every integration test
        - Truncate jobs table
        """
        truncate_clause: TextClause = text("TRUNCATE TABLE jobs CASCADE")
        async with engine.begin() as connection:
            await connection.execute(truncate_clause)

    @staticmethod
    async def clear_raw_search_results_table() -> None:
        """
        Runs at the start of every integration test
        - Truncate raw search results table
        """
        truncate_clause: TextClause = text("TRUNCATE TABLE raw_search_results")
        async with engine.begin() as connection:
            await connection.execute(truncate_clause)

    @staticmethod
    async def clear_extracted_search_results_table() -> None:
        """
        Runs at the start of every integration test
        - Truncate extracted search results table
        """
        truncate_clause: TextClause = text("TRUNCATE TABLE extracted_search_results")
        async with engine.begin() as connection:
            await connection.execute(truncate_clause)
