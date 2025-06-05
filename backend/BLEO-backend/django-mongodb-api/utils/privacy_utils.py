import re
from typing import Optional, Union

class PrivacyUtils:
    """Utility functions for data privacy and masking"""
    
    @staticmethod
    def mask_email(email: Optional[str]) -> str:
        """
        Mask email for logging purposes while preserving readability
        
        Args:
            email (str): Email address to mask
            
        Returns:
            str: Masked email address
            
        Examples:
            - a@example.com → a@example.com (single char, no masking)
            - ab@example.com → a*@example.com (2 chars: first + asterisk)
            - abc@example.com → a*c@example.com (3 chars: first + asterisk + last)
            - test@example.com → te*t@example.com (4 chars: first two + asterisk + last)
            - hello@example.com → he**o@example.com (5+ chars: first two + two asterisks + last)
            - verylongname@example.com → ve**e@example.com (very long: first two + two asterisks + last)
        """
        try:
            if not email or not isinstance(email, str) or '@' not in email:
                return "invalid-email"
                
            parts = email.split('@')
            if len(parts) != 2:
                return "invalid-email"
                
            username = parts[0]
            domain = parts[1]
            
            if not username or not domain:
                return "invalid-email"
            
            # Handle different username lengths
            if len(username) == 1:
                # Single character: don't mask
                masked_username = username
            elif len(username) == 2:
                # Two characters: mask second character
                masked_username = username[0] + '*'
            elif len(username) == 3:
                # Three characters: first + asterisk + last
                masked_username = username[0] + '*' + username[-1]
            elif len(username) == 4:
                # Four characters: first two + asterisk + last
                masked_username = username[0:2] + '*' + username[-1]
            else:
                # Five or more characters: first two + two asterisks + last
                masked_username = username[0:2] + '**' + username[-1]
                
            return f"{masked_username}@{domain}"
            
        except Exception:
            return "invalid-email"
    
    @staticmethod
    def mask_phone(phone: Optional[str]) -> str:
        """
        Mask phone number for logging purposes
        
        Args:
            phone (str): Phone number to mask
            
        Returns:
            str: Masked phone number
            
        Examples:
            - +1234567890 → +123****890
            - 1234567890 → 123****890
            - 12345 → 12*45
        """
        try:
            if not phone or not isinstance(phone, str):
                return "invalid-phone"
            
            # Remove non-digit characters except +
            cleaned = re.sub(r'[^\d+]', '', phone)
            
            if len(cleaned) < 4:
                return "invalid-phone"
            
            if len(cleaned) <= 6:
                return cleaned[0:2] + '*' * (len(cleaned) - 2)
            else:
                return cleaned[0:3] + '*' * (len(cleaned) - 6) + cleaned[-3:]
                
        except Exception:
            return "invalid-phone"
    
    @staticmethod
    def mask_credit_card(card_number: Optional[str]) -> str:
        """
        Mask credit card number for logging purposes
        
        Args:
            card_number (str): Credit card number to mask
            
        Returns:
            str: Masked credit card number
            
        Examples:
            - 1234567890123456 → 1234****3456
            - 4111-1111-1111-1111 → 4111-****-****-1111
        """
        try:
            if not card_number or not isinstance(card_number, str):
                return "invalid-card"
            
            # Remove non-digit characters
            digits_only = re.sub(r'\D', '', card_number)
            
            if len(digits_only) < 8:
                return "invalid-card"
            
            # Keep first 4 and last 4 digits, mask the rest
            if len(digits_only) <= 8:
                return digits_only[0:2] + '*' * (len(digits_only) - 4) + digits_only[-2:]
            else:
                return digits_only[0:4] + '*' * (len(digits_only) - 8) + digits_only[-4:]
                
        except Exception:
            return "invalid-card"
    
    @staticmethod
    def mask_name(name: Optional[str]) -> str:
        """
        Mask personal name for logging purposes
        
        Args:
            name (str): Personal name to mask
            
        Returns:
            str: Masked name
            
        Examples:
            - John → J***
            - John Doe → J*** D**
            - Mary Jane Smith → M*** J*** S****
        """
        try:
            if not name or not isinstance(name, str):
                return "invalid-name"
            
            # Split name into parts
            name_parts = name.strip().split()
            
            if not name_parts:
                return "invalid-name"
            
            masked_parts = []
            for part in name_parts:
                if len(part) == 1:
                    masked_parts.append(part)
                elif len(part) == 2:
                    masked_parts.append(part[0] + '*')
                else:
                    masked_parts.append(part[0] + '*' * (len(part) - 1))
            
            return ' '.join(masked_parts)
            
        except Exception:
            return "invalid-name"
    
    @staticmethod
    def mask_address(address: Optional[str]) -> str:
        """
        Mask address for logging purposes
        
        Args:
            address (str): Address to mask
            
        Returns:
            str: Masked address
            
        Examples:
            - 123 Main Street → 123 M*** S*****
            - 456 Oak Avenue, Apt 2B → 456 O** A*****, A** 2*
        """
        try:
            if not address or not isinstance(address, str):
                return "invalid-address"
            
            # Keep numbers and first letter of each word
            words = address.split()
            masked_words = []
            
            for word in words:
                # Keep numbers as is
                if word.isdigit():
                    masked_words.append(word)
                # Keep short words (2 chars or less) as is
                elif len(word) <= 2:
                    masked_words.append(word)
                # Mask longer words
                else:
                    # Remove punctuation for masking, but keep it
                    clean_word = re.sub(r'[^\w]', '', word)
                    if clean_word:
                        masked_clean = clean_word[0] + '*' * (len(clean_word) - 1)
                        # Put punctuation back
                        masked_word = word
                        for i, char in enumerate(word):
                            if char.isalnum() and i < len(masked_clean):
                                masked_word = masked_word[:i] + masked_clean[min(i, len(masked_clean)-1)] + masked_word[i+1:]
                        masked_words.append(masked_word)
                    else:
                        masked_words.append(word)
            
            return ' '.join(masked_words)
            
        except Exception:
            return "invalid-address"
    
    @staticmethod
    def mask_sensitive_data(data: Union[str, int, float], field_name: str) -> str:
        """
        Generic function to mask sensitive data based on field type
        
        Args:
            data: Data to mask
            field_name (str): Name of the field to determine masking strategy
            
        Returns:
            str: Masked data
            
        Examples:
            - mask_sensitive_data("test@example.com", "user_email") → "te**t@example.com"
            - mask_sensitive_data("1234567890", "phone_number") → "123****890"
            - mask_sensitive_data("secret123", "password") → "***[HIDDEN]***"
        """
        try:
            if data is None:
                return "null-value"
            
            data_str = str(data)
            field_lower = field_name.lower()
            
            # Determine masking strategy based on field name
            if any(keyword in field_lower for keyword in ['email', 'mail']):
                return PrivacyUtils.mask_email(data_str)
            elif any(keyword in field_lower for keyword in ['phone', 'mobile', 'tel']):
                return PrivacyUtils.mask_phone(data_str)
            elif any(keyword in field_lower for keyword in ['card', 'credit', 'payment']):
                return PrivacyUtils.mask_credit_card(data_str)
            elif any(keyword in field_lower for keyword in ['name', 'firstname', 'lastname']):
                return PrivacyUtils.mask_name(data_str)
            elif any(keyword in field_lower for keyword in ['address', 'street', 'location']):
                return PrivacyUtils.mask_address(data_str)
            elif any(keyword in field_lower for keyword in ['password', 'secret', 'token', 'key', 'auth']):
                return "***[HIDDEN]***"
            elif any(keyword in field_lower for keyword in ['ssn', 'social', 'tax', 'id']):
                return "***[PROTECTED]***"
            else:
                # Generic masking for other sensitive fields
                if len(data_str) <= 4:
                    return '*' * len(data_str)
                else:
                    return data_str[0:2] + '*' * max(0, len(data_str) - 4) + data_str[-2:]
                    
        except Exception:
            return "invalid-data"
    
    @staticmethod
    def is_sensitive_field(field_name: str) -> bool:
        """
        Check if a field name indicates sensitive data
        
        Args:
            field_name (str): Field name to check
            
        Returns:
            bool: True if field is likely sensitive
        """
        if not field_name or not isinstance(field_name, str):
            return False
        
        field_lower = field_name.lower()
        
        sensitive_keywords = [
            'password', 'secret', 'token', 'key', 'auth',
            'email', 'mail', 'phone', 'mobile', 'tel',
            'card', 'credit', 'payment', 'account',
            'ssn', 'social', 'tax', 'id',
            'name', 'firstname', 'lastname',
            'address', 'street', 'location',
            'birth', 'dob', 'age'
        ]
        
        return any(keyword in field_lower for keyword in sensitive_keywords)
    
    @staticmethod
    def mask_object(obj: dict, sensitive_fields: Optional[list] = None) -> dict:
        """
        Mask sensitive fields in a dictionary object
        
        Args:
            obj (dict): Object to mask
            sensitive_fields (list, optional): List of field names to mask
            
        Returns:
            dict: Object with masked sensitive fields
        """
        try:
            if not isinstance(obj, dict):
                return obj
            
            masked_obj = obj.copy()
            
            for key, value in masked_obj.items():
                # Check if field should be masked
                should_mask = False
                
                if sensitive_fields and key in sensitive_fields:
                    should_mask = True
                elif PrivacyUtils.is_sensitive_field(key):
                    should_mask = True
                
                if should_mask and value is not None:
                    masked_obj[key] = PrivacyUtils.mask_sensitive_data(value, key)
            
            return masked_obj
            
        except Exception:
            return obj

    @staticmethod
    def is_valid_email(email: Optional[str]) -> bool:
        """
        Comprehensive email validation with multiple checks
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if email format is valid and passes all checks
            
        Examples:
            - is_valid_email("test@example.com") → True
            - is_valid_email("invalid-email") → False
            - is_valid_email("test@") → False
            - is_valid_email("@example.com") → False
            - is_valid_email("test.email+tag@domain.co.uk") → True
        """
        try:
            if not email or not isinstance(email, str):
                return False
            
            # Remove leading/trailing whitespace
            email = email.strip()
            
            # Basic length checks
            if len(email) < 5 or len(email) > 254:  # RFC 5321 limit
                return False
            
            # Must contain exactly one @ symbol
            if email.count('@') != 1:
                return False
            
            # Split into local and domain parts
            local_part, domain_part = email.split('@')
            
            # Validate local part (before @)
            if not PrivacyUtils._validate_email_local_part(local_part):
                return False
            
            # Validate domain part (after @)
            if not PrivacyUtils._validate_email_domain_part(domain_part):
                return False
            
            # Additional comprehensive regex check
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def _validate_email_local_part(local_part: str) -> bool:
        """
        Validate the local part (username) of an email address
        
        Args:
            local_part (str): The part before @ in email
            
        Returns:
            bool: True if local part is valid
        """
        try:
            if not local_part or len(local_part) < 1 or len(local_part) > 64:  # RFC 5321 limit
                return False
            
            # Cannot start or end with a dot
            if local_part.startswith('.') or local_part.endswith('.'):
                return False
            
            # Cannot have consecutive dots
            if '..' in local_part:
                return False
            
            # Check allowed characters
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-')
            if not all(char in allowed_chars for char in local_part):
                return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def _validate_email_domain_part(domain_part: str) -> bool:
        """
        Validate the domain part of an email address
        
        Args:
            domain_part (str): The part after @ in email
            
        Returns:
            bool: True if domain part is valid
        """
        try:
            if not domain_part or len(domain_part) < 1 or len(domain_part) > 253:  # RFC 5321 limit
                return False
            
            # Cannot start or end with a dot or hyphen
            if domain_part.startswith('.') or domain_part.endswith('.'):
                return False
            if domain_part.startswith('-') or domain_part.endswith('-'):
                return False
            
            # Must contain at least one dot (for TLD)
            if '.' not in domain_part:
                return False
            
            # Split into labels (parts separated by dots)
            labels = domain_part.split('.')
            
            # Must have at least 2 labels (domain + TLD)
            if len(labels) < 2:
                return False
            
            # Validate each label
            for label in labels:
                if not PrivacyUtils._validate_domain_label(label):
                    return False
            
            # Last label (TLD) must be at least 2 characters and contain only letters
            tld = labels[-1]
            if len(tld) < 2 or not tld.isalpha():
                return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def _validate_domain_label(label: str) -> bool:
        """
        Validate a single domain label (part between dots)
        
        Args:
            label (str): Domain label to validate
            
        Returns:
            bool: True if label is valid
        """
        try:
            if not label or len(label) < 1 or len(label) > 63:  # RFC 1035 limit
                return False
            
            # Cannot start or end with hyphen
            if label.startswith('-') or label.endswith('-'):
                return False
            
            # Check allowed characters (alphanumeric and hyphens)
            allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-')
            if not all(char in allowed_chars for char in label):
                return False
            
            return True
            
        except Exception:
            return False

    @staticmethod
    def validate_email_format(email: Optional[str]) -> bool:
        """
        Alias for is_valid_email for backward compatibility
        
        Args:
            email (str): Email to validate
            
        Returns:
            bool: True if email format is valid
        """
        return PrivacyUtils.is_valid_email(email)

    @staticmethod
    def validate_email_list(emails: list) -> dict:
        """
        Validate a list of email addresses
        
        Args:
            emails (list): List of email addresses to validate
            
        Returns:
            dict: Results with valid/invalid emails and details
            
        Example:
            validate_email_list(["valid@test.com", "invalid-email", "another@valid.com"])
            → {
                "valid_emails": ["valid@test.com", "another@valid.com"],
                "invalid_emails": ["invalid-email"],
                "total_count": 3,
                "valid_count": 2,
                "invalid_count": 1,
                "validation_rate": 66.67
            }
        """
        try:
            if not isinstance(emails, list):
                return {
                    "valid_emails": [],
                    "invalid_emails": [],
                    "total_count": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "validation_rate": 0.0,
                    "error": "Input must be a list"
                }
            
            valid_emails = []
            invalid_emails = []
            
            for email in emails:
                if PrivacyUtils.is_valid_email(email):
                    valid_emails.append(email)
                else:
                    invalid_emails.append(email)
            
            total_count = len(emails)
            valid_count = len(valid_emails)
            invalid_count = len(invalid_emails)
            validation_rate = (valid_count / total_count * 100) if total_count > 0 else 0.0
            
            return {
                "valid_emails": valid_emails,
                "invalid_emails": invalid_emails,
                "total_count": total_count,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "validation_rate": round(validation_rate, 2)
            }
            
        except Exception as e:
            return {
                "valid_emails": [],
                "invalid_emails": [],
                "total_count": 0,
                "valid_count": 0,
                "invalid_count": 0,
                "validation_rate": 0.0,
                "error": str(e)
            }

    @staticmethod
    def get_email_domain(email: Optional[str]) -> Optional[str]:
        """
        Extract domain from email address
        
        Args:
            email (str): Email address
            
        Returns:
            str: Domain part of email, or None if invalid
            
        Examples:
            - get_email_domain("test@example.com") → "example.com"
            - get_email_domain("invalid-email") → None
        """
        try:
            if not PrivacyUtils.is_valid_email(email):
                return None
            
            return email.split('@')[1].lower()
            
        except Exception:
            return None

    @staticmethod
    def normalize_email(email: Optional[str]) -> Optional[str]:
        """
        Normalize email address (lowercase, trim whitespace)
        
        Args:
            email (str): Email address to normalize
            
        Returns:
            str: Normalized email, or None if invalid
            
        Examples:
            - normalize_email("  TEST@Example.COM  ") → "test@example.com"
            - normalize_email("invalid-email") → None
        """
        try:
            if not email or not isinstance(email, str):
                return None
            
            # Trim and convert to lowercase
            normalized = email.strip().lower()
            
            # Validate normalized email
            if not PrivacyUtils.is_valid_email(normalized):
                return None
            
            return normalized
            
        except Exception:
            return None