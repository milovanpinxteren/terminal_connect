from django.db import models


class TerminalLinks(models.Model):
    """Links Shopify POS sessions to Pin Vandaag terminals"""
    shop_id = models.CharField(max_length=255, blank=True, null=True)
    user_id = models.CharField(max_length=255, blank=True, null=True)
    shop_domain = models.CharField(max_length=255, db_index=True)
    location_id = models.CharField(max_length=255, blank=True, null=True)
    staff_member_id = models.CharField(max_length=255, blank=True, null=True)
    terminal_id = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Terminal Links"

    def __str__(self):
        return f"{self.shop_domain} -> {self.terminal_id}"


class Transaction(models.Model):
    """Logs all transactions for debugging and reconciliation"""
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]

    transaction_id = models.CharField(max_length=255, db_index=True)
    terminal_link = models.ForeignKey(TerminalLinks, on_delete=models.SET_NULL, null=True)
    amount = models.IntegerField(help_text="Amount in cents")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started')
    error_msg = models.TextField(blank=True, null=True)
    receipt = models.TextField(blank=True, null=True)
    shop_domain = models.CharField(max_length=255)
    location_id = models.CharField(max_length=255, blank=True, null=True)
    staff_member_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"
