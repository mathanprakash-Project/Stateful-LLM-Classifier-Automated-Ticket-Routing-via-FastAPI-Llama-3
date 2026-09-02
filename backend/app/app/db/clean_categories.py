"""
Database cleanup script to remove non-application categories and keep strictly:
1. Application UI
2. Application Version Maintenance
3. Client Data Transfer
4. File Management
"""
import asyncio
from sqlalchemy import select, update, delete
from app.db.session import AsyncSessionLocal
from app.models import TicketCategory, TicketSubcategory, Ticket

async def clean_categories():
    async with AsyncSessionLocal() as session:
        # 1. Get or create Application UI as fallback
        stmt = select(TicketCategory).where(TicketCategory.name == "Application UI")
        res = await session.execute(stmt)
        ui_cat = res.scalar_one_or_none()
        if not ui_cat:
            ui_cat = TicketCategory(name="Application UI", description="Application UI Changes / Issues")
            session.add(ui_cat)
            await session.flush()

        # 2. Non-application category names to remove
        non_app_names = [
            "Server / Infrastructure",
            "Database",
            "Network",
            "Security",
            "Other Technical",
            "Application Support",
            "General Support",
            "General"
        ]

        for name in non_app_names:
            stmt_cat = select(TicketCategory).where(TicketCategory.name == name)
            res_cat = await session.execute(stmt_cat)
            cat = res_cat.scalar_one_or_none()
            if cat:
                print(f"Cleaning up non-application category: {cat.name} ({cat.id})")
                # Reassign tickets referencing this category to Application UI
                await session.execute(
                    update(Ticket).where(Ticket.category_id == cat.id).values(category_id=ui_cat.id)
                )
                # Delete subcategories
                await session.execute(
                    delete(TicketSubcategory).where(TicketSubcategory.category_id == cat.id)
                )
                # Delete category
                await session.delete(cat)

        await session.commit()
        print("Cleanup completed successfully!")

if __name__ == "__main__":
    asyncio.run(clean_categories())

