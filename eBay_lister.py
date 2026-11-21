
import os
from ebaysdk.trading import Connection as Trading
from ebaysdk.exception import ConnectionError
from PIL import Image
import configparser
import logging

class EbayLister:
    def __init__(self):
        """Initialize the eBay API connection using credentials from config file"""
        self.config = self._load_config()
        self.api = Trading(config_file='ebay.yaml', domain='api.ebay.com')
        self.setup_logging()

    def _load_config(self):
        """Load eBay API credentials from configuration file"""
        config = configparser.ConfigParser()
        config_path = 'config.ini'
       
        if not os.path.exists(config_path):
            self._create_default_config(config_path)
            raise FileNotFoundError(
                "Please fill in your eBay API credentials in config.ini"
            )
       
        config.read(config_path)
        return config

    def _create_default_config(self, config_path):
        """Create a template configuration file"""
        config = configparser.ConfigParser()
        config['eBay'] = {
            'api_key': 'YOUR_API_KEY',
            'cert_id': 'YOUR_CERT_ID',
            'dev_id': 'YOUR_DEV_ID',
            'token': 'YOUR_TOKEN'
        }
       
        with open(config_path, 'w') as f:
            config.write(f)

    def setup_logging(self):
        """Configure logging for the application"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ebay_lister.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def validate_image(self, image_path):
        """
        Validate if the image meets eBay's requirements
        Returns: tuple (is_valid, error_message)
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                format = img.format
                filesize = os.path.getsize(image_path) / (1024 * 1024)  # Size in MB

                if format not in ['JPEG', 'PNG']:
                    return False, "Image must be JPEG or PNG format"
                if filesize > 12:
                    return False, "Image size must be less than 12MB"
                if width < 500 or height < 500:
                    return False, "Image dimensions must be at least 500x500 pixels"
               
                return True, "Image is valid"
        except Exception as e:
            return False, f"Error validating image: {str(e)}"

    def create_item_listing(self, image_path, price, title, description="", category_id=""):
        """
        Create a new item listing on eBay
       
        Parameters:
        - image_path: Path to the image file
        - price: Price of the item (float)
        - title: Title of the listing
        - description: Optional item description
        - category_id: Optional eBay category ID
        """
        try:
            # Validate image first
            is_valid, message = self.validate_image(image_path)
            if not is_valid:
                self.logger.error(f"Image validation failed: {message}")
                return False, message

            # Prepare the item dictionary
            item = {
                "Item": {
                    "Title": title,
                    "Description": description,
                    "PrimaryCategory": {"CategoryID": category_id if category_id else "11450"},
                    "StartPrice": str(price),
                    "CategoryMappingAllowed": "true",
                    "Country": "US",
                    "ConditionID": "1000",
                    "Currency": "USD",
                    "DispatchTimeMax": "3",
                    "ListingDuration": "Days_7",
                    "ListingType": "FixedPriceItem",
                    "PaymentMethods": "PayPal",
                    "PayPalEmailAddress": self.config['eBay']['paypal_email'],
                    "PictureDetails": {
                        "PictureURL": []
                    },
                    "PostalCode": self.config['eBay']['postal_code'],
                    "Quantity": "1",
                    "ReturnPolicy": {
                        "ReturnsAcceptedOption": "ReturnsAccepted",
                        "RefundOption": "MoneyBack",
                        "ReturnsWithinOption": "Days_30",
                        "ShippingCostPaidByOption": "Buyer"
                    },
                    "ShippingDetails": {
                        "ShippingType": "Flat",
                        "ShippingServiceOptions": {
                            "ShippingServicePriority": "1",
                            "ShippingService": "USPSPriority",
                            "ShippingServiceCost": "0.00"
                        }
                    },
                    "Site": "US"
                }
            }

            # Upload the image first
            with open(image_path, 'rb') as f:
                image_data = f.read()
           
            # Upload image to eBay
            picture_response = self.api.execute('UploadSiteHostedPictures', {
                'PictureName': os.path.basename(image_path),
                'PictureData': image_data
            })
           
            # Add the uploaded image URL to the item dictionary
            item["Item"]["PictureDetails"]["PictureURL"].append(
                picture_response.response.dict()['SiteHostedPictureDetails']['FullURL']
            )

            # Create the listing
            response = self.api.execute('AddFixedPriceItem', item)
           
            listing_id = response.reply.ItemID
            self.logger.info(f"Successfully created listing with ID: {listing_id}")
            return True, f"Listing created successfully. Item ID: {listing_id}"

        except ConnectionError as e:
            error_message = f"eBay API connection error: {e.response.dict()}"
            self.logger.error(error_message)
            return False, error_message
        except Exception as e:
            error_message = f"Error creating listing: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

def main():
    """Main function to run the program"""
    try:
        lister = EbayLister()
       
        # Get input from user
        image_path = input("Enter the path to your image file: ")
        price = float(input("Enter the price for your item: $"))
        title = input("Enter the title for your listing: ")
        description = input("Enter a description (optional): ")
       
        # Create the listing
        success, message = lister.create_item_listing(
            image_path=image_path,
            price=price,
            title=title,
            description=description
        )
       
        if success:
            print(f"Success! {message}")
        else:
            print(f"Failed to create listing: {message}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 
