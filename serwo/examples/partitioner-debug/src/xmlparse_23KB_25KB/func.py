from xml.dom.minidom import parse, parseString
from python.src.utils.classes.commons.serwo_objects import SerWOObject

def function(serwoObject) -> SerWOObject:
    try:
        ret_str_25KB = "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"
        # body = serwoObject.get_body()
        print("xml start")
        document = parseString("""<?xml version='1.0' ?>
<!DOCTYPE root SYSTEM "http://www.cs.washington.edu/research/projects/xmltk/xmldata/data/auctions/321gone.dtd">
<root>
                   <listing>
   <seller_info>
       <seller_name>537_sb_3 </seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>Visa, Mastercard, , , , 0, Discover, American Express
   </payment_types>
   <shipping_info>siteonly, Buyer Pays Shipping Costs
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $839.93</current_bid>
     <time_left> 1 Day, 6 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 5</num_items>
     <num_bids>  0</num_bids>
     <started_at> $839.93</started_at>
     <bid_increment> </bid_increment>
     <location> Englewood , Utah, United States</location>
     <opened> 11/25/00 7:46:16 PM</opened>
     <closed> 11/28/00 7:46:16 PM</closed>
     <id_num> 315914 </id_num>
     <notes> </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>839.93
       </highest_bid_amount>
       <quantity>0 </quantity>
   </bid_history>
   <item_info>
      <memory> </memory>
      <hard_drive> </hard_drive>
      <cpu> </cpu>
      <brand> </brand>
      <description>AMD Athlon 900 Mhz Processor. New K7 CPU comes with a year warranty. Rated gamers paradise in all reviews and high benchmark ratings.
Days To Ship: 5




 
      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name> lapro8</seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>Money Order
   </payment_types>
   <shipping_info>International Shipping, See Shipping Description
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $210.00</current_bid>
     <time_left> 4 Days, 21 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 1</num_items>
     <num_bids>  0</num_bids>
     <started_at> $210.00</started_at>
     <bid_increment> $5.00</bid_increment>
     <location>Cherkasy, Ukraine </location>
     <opened> 11/27/00 11:15:34 AM</opened>
     <closed> 12/2/00 11:15:34 AM</closed>
     <id_num> 320761</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$210.00
       </highest_bid_amount>
       <quantity>0 </quantity>
   </bid_history>
   <item_info>
      <memory> 64MB Ram(Maximum - 256 MB)</memory>
      <hard_drive> 4 GB  Removable Hard Drive</hard_drive>
      <cpu> Intel Pentium II 266MHZ MMX</cpu>
      <brand> Compaq</brand>
      <description> Compaq Armada 7400 

Intel Pentium II  266MHZ MMX LAPTOP!!!!

This laptop looks and feels solid! The screen is huge, the keyboard feels good, the mouse moves just right! 

 Internet Ready!  

Its Features are as Follows:

Intel Mobile PentiumR II processor 266 MHz- very fast!!

512KB L2 Cache

64MB Ram (Maximum - 256 MB )

4 GB  Removable Hard Drive

13.3 CTFT 1024 x 768 panel ( huge and very nice!)

 

Windows 95 included!!

AGP implementation with dedicated 66-MHz graphics bus. Frame mode support S3 ViRGE/MXTM graphics controller with 4 MB of 100 MHz SGRAM. Up to 100 Hz external refresh at SVGA resolution up to 16.8 million colors. Simultaneous display support in any resolutions.

16-bit Compaq PremierSoundTM and Hardware Wave Table for enhanced audio (16-bit Sound Blaster Pro compatible), integrated stereo speakers and Bass Reflex speaker ports, integrated microphone, hardware and software volume control, headphone, microphone and stereo line-in jacks, standard CD-ROM or DVD-ROM Drive, software MPEG1 and software MPEG2 available (sounds crisp)

AC Adapter and Battery works (but the life of the battery is not warranted) 
3.5 Floppy Drive (swappable) 
24X CD-ROM (swappable) 
MORE INFO:

PC Card Slots

Two Type II/One Type III PC Card Slot(s), which support both 32-bit CardBus9 and 16-bit PC Cards; Zoomed Video support in bottom slot only; telephony support in top slot only

Interfaces

PC Card Two Type II/One Type III 
Enhanced Parallel 1 
Serial 1 
External Monitor 1 
External Keyboard/Pointing Device (PS/2) 1 
Convenience Base 1 
Headphone/Line out 1 
Stereo Line In 1 
Microphone 1 
AC Power 1 
RJ 11 1 
Infrared 1 (4 Mb/s10 support) 
Expansion Base 1 
USB 1 
Support for Third-Party Y-Cables
(for external mouse and keyboard) Yes 

Buyer have to pay by money order. Please add $30 for shipping (includes insurance) International shipping additional. 

      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name> aboutlaw</seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>American Express, Discover, MasterCard, Visa
   </payment_types>
   <shipping_info>Other Shipping Service, UPS
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid>  $1,049.00 </current_bid>
     <time_left> 5 Days, 20 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 9</num_items>
     <num_bids> 0 </num_bids>
     <started_at>$1,049.00 </started_at>
     <bid_increment> </bid_increment>
     <location> seattel, Washington, United States</location>
     <opened> 11/18/00 9:42:39 AM</opened>
     <closed> 12/3/00 9:42:39 AM</closed>
     <id_num> 299664</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$1,049.00
       </highest_bid_amount>
       <quantity> 0</quantity>
   </bid_history>
   <item_info>
      <memory> 64MB</memory>
      <hard_drive> 20GB</hard_drive>
      <cpu> Celeron 600MHz</cpu>
      <brand> </brand>
      <description> Computers, desktops, printers, software 
Great prices and great value on all computers:

WebPC CeleronAMD Athlon 900 Mhz Processor. New K7 CPU comes with a year warranty. Rated gamers paradise in all reviews and high benchmark ratings.
Days To Ship: 5



We gladly accept:    

Not quite what you are looking for? See our similar products currently up for bid.

Have a question about Shipping, Returns Policy, Our Company or anything else? Click Here. 600MHz Computer Bundle with 17 Monitor
600MHz / 64MB / 20GB / 50x CD-ROM / 4x4x32 CD-RW / 56k / 17 Monitor
This package gives you a high-performance computer and 17 monitor an amazingly affordable price. The computer, a WebPC, has a 600MHz Intel. Celeron. processor, a 20GB hard drive, and 64 MB 100MHz SDRAM to keep your machine moving quick... [more]
After Rebate: $999.00

 

      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name>1137_sb_8 </seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>Visa, Mastercard, Personal Check, MOney Order, , 0, , American Express
   </payment_types>
   <shipping_info>Irving, Utah, United States
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> No Bids</current_bid>
     <time_left> 1 Day, 2 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 1</num_items>
     <num_bids>  0</num_bids>
     <started_at> $650.00</started_at>
     <bid_increment> $10.00</bid_increment>
     <location> Irving, Utah, United States</location>
     <opened> 11/25/00 3:42:50 PM</opened>
     <closed> 11/28/00 3:42:50 PM</closed>
     <id_num> 314115</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>No Bids
       </highest_bid_amount>
       <quantity> 0</quantity>
   </bid_history>
   <item_info>
      <memory> 32MB RAM</memory>
      <hard_drive> 2.1GB hard driv</hard_drive>
      <cpu> Pentium 166</cpu>
      <brand> </brand>
      <description> Pentium 166, 32MB RAM, 2.1GB hard drive, cd-rom drive, Floppy drive, 12.1' TFT Color Screen, Battery and AC Adapter, 28.8K integrated modem. Fully licensed Windows 95 pre-installed for your convenience. This usedl aptop is Internet Ready. Add 16MB for $48 and 32MB more for $110. Upgrade to 56K modem for $65.


      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name> 537_sb_3</seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>Visa, Mastercard, , , , 0, Discover, American Express
   </payment_types>
   <shipping_info>siteonly, Buyer Pays Shipping Costs
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $657.52</current_bid>
     <time_left> 1 Day, 4 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 5</num_items>
     <num_bids>  0</num_bids>
     <started_at> $657.52</started_at>
     <bid_increment> </bid_increment>
     <location> Englewood , Utah, United States</location>
     <opened> 11/25/00 5:24:20 PM</opened>
     <closed> 11/28/00 5:24:20 PM</closed>
     <id_num> 314815</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$657.52 </highest_bid_amount>
       <quantity>0 </quantity>
   </bid_history>
   <item_info>
      <memory> </memory>
      <hard_drive> </hard_drive>
      <cpu> </cpu>
      <brand> </brand>
      <description> 
We gladly accept:    

Not quite what you are looking for? See our similar products currently up for bid.

Have a question about Shipping, Returns Policy, Our Company or anything else? Click Here.

      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name>42_sb_691 </seller_name>
       <seller_rating> 1</seller_rating>
   </seller_info>
   <payment_types>Visa, Mastercard, Personal Check, , , 0, Discover, American Express
   </payment_types>
   <shipping_info>International Shipping, Buyer Pays Shipping Costs
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $2,631.00</current_bid>
     <time_left> 1 Day, 4 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 3</num_items>
     <num_bids>  0</num_bids>
     <started_at> $2,631.00</started_at>
     <bid_increment> </bid_increment>
     <location> Indianapolis, Utah, United States</location>
     <opened> 11/25/00 5:54:53 PM</opened>
     <closed> 11/28/00 5:54:53 PM</closed>
     <id_num> 315092</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$2,631.00
       </highest_bid_amount>
       <quantity> 0</quantity>
   </bid_history>
   <item_info>
      <memory> 64 MB</memory>
      <hard_drive> 12 GB</hard_drive>
      <cpu> 650 MHz</cpu>
      <brand> Hewlett-Packard </brand>
      <description> Manufacturer Part #

Manufacturer
Hewlett-Packard 
System: Type
Portable 
System: Form Factor
Notebook 
System: BIOS
Vendor Specific 
Processor: Installed Brand
Intel 
Processor: Class
Intel Pentium III 
Processor: Speed (MHz)
650 MHz 
Processor: Max Upgrade Supported (MHz)
Not Upgradable 
Processor: Brands Supported
Intel 
Processor: Max Number Supported
Single Processor 
Processor: Socket Type/Chipset
Pin Grid Array (PGA) Socket 
Memory: Installed Amount
64 MB 
Memory: Max Amount Supported
192 MB 
Memory: Type/Style Installed/Supported
SDRAM 
Memory: Number of Pins
Vendor Specific 
Memory: Number of Sockets
(2) Vendor Specific 
Memory: Speed
Vendor Specific 
Memory: Must Be Added In
Singles 
Cache: Installed Amount
256 KB 
Synchronous 
Pipeline Burst 
Cache: Max Amount
256 KB 
Hard Drive: Formatted Capacity
12 GB 
Hard Drive: Type Interface
EIDE 
Other Storage
1.44 MB Floppy Drive 
Device Controller: Type Included
Integrated 
Device Controller: Bus Type
Integrated 
Device Controller: Cable Included
Yes 
Communication: Fax/Modem
None Included 
Communication: Network
None Included 
Keyboard
87 Key Integrated Keyboard 
Pointing Device
Integrated Trackstick 
Integrated TouchPad 
Video Card: Bus Type
AGP 
Integrated 
Video Card: Manufacturer/Chipset
2D/3D Graphics Accelerator 
Video Card: Max Standard/Max Resolution
XGA 
1024 x 768 
Video Card: Memory Amount Included
2.5 MB 
Video Card: Max Memory Supported
Not Upgradeable 
Video Card: Memory Type
VRAM 
Video Card: Features
MPEG II 
Zoomed Video (ZV) Port 
Notebook Display: Type Screen
13.3in Diagonal 
Active TFT Matrix 
Dimensions:
11.8 W 8.8 W 1.26 in (30 W 22.5 W 3.2 cm) or 11.95 x 9.3 x 1.4 in (30.4 x 23.7 x 3.5 cm) 
Weight:
4.0 lb (1.79 kg) 
Notebook Display: Max Resolution
1024 x 768 
Built-in Audio Features
Built-in Microphone 
Built-in 16-bit Stereo Audio Product Code: NBKHP136
      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name> 42_sb_691</seller_name>
       <seller_rating> 1</seller_rating>
   </seller_info>
   <payment_types>Visa, Mastercard, Personal Check, , , 0, Discover, American Express
   </payment_types>
   <shipping_info>International Shipping, Buyer Pays Shipping Costs
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $2,618.00</current_bid>
     <time_left> 1 Day, 8 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 3</num_items>
     <num_bids>  0</num_bids>
     <started_at> 11/25/00 9:58:02 PM</started_at>
     <bid_increment> </bid_increment>
     <location> Indianapolis, Utah, United States</location>
     <opened> 11/25/00 9:58:02 PM</opened>
     <closed> 11/28/00 9:58:02 PM</closed>
     <id_num> 316215</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$2,618.00
       </highest_bid_amount>
       <quantity> 0</quantity>
   </bid_history>
   <item_info>
      <memory> 64Mbit SDRAM, expandable to 320MB 3.3V, 60ns</memory>
      <hard_drive> 12 GB hard disk drive</hard_drive>
      <cpu> Mobile Intel. 700 MHz Pentium. III processor featuring Intel SpeedStep</cpu>
      <brand> </brand>
      <description>
Display
15. 0 diagonal (1024 x 768)
Internal display supports up to 16M colors at
800 x 600 and 64K colors at 1024 x 768 
External Color Support
    800 x 600 and 640 x 480; 60/70/85Hz Non-Interlaced @ 16M
    1024 x 768; 60Hz Non-Interlaced @ 16M
    1600 x 1200; 60Hz Non-Interlaced @ 64K 
Processor
Mobile Intel. 700 MHz Pentium. III processor featuring Intel SpeedStepVisa, Mastercard, Personal Check, , , 0, Discover, American Express Technology.
100MHz Front Side Bus
Data/Address Bus Width: 64-bit/32-bit
Integrated co-processor 
Cache Memory
256KB Level 2 cache integrated on die
32KB internal cache 
System Memory
64Mbit SDRAM, expandable to 320MB 3.3V, 60ns
Internal memory expansion slot 
BIOS
    APM V1.2; ACPI V1.2; PnP V1.0a; VESA V2.0; DPMS; DDC2B; DMI 2.0, SM BIOS V2.3, PCI BIOS V2.2 
System Architecture
PCI Bus V2.2 
Keyboard
Full sized 85 keys with 12 function keys 
Pointing Device
Integrated AccuPoint. II pointing device with scroll buttons 
Communications
Integrated V.90/K56flex modem 
Storage Drive
    12 GB hard disk drive
-13ms average access time
-Supports PIO Mode4 or Ultra DMA33 Mode2
    Built-in 6X max. speed DVD-ROM (130 ms access time)
    integrated 3.5-inch, 1.44-MB floppy disk drive 
Video
S3 Savage IX Graphics Controller
64-BIT graphics accelerator 2x AGP bus
128 BitBLT hardware
8MB internal video memory 
Audio
Yamaha YMF744B-R 3D sound support with HRTF 3D positional audio
16-bit stereo, .WAV and Sound Blaster. Pro compatible, MIDI playback
2 built-in stereo speakers
64-channel wavetable music synthesis
Full duplex sound support
Hardware acceleration for DirectMusic and
DirectSound
Microphone and Headphone ports 
Expansion
Two PC Card slots support two Type II or one
    Type III PC Cards; 32-bit CardBus ready
SVGA video port
Fast infrared port (4Mbps, IrDA V1.1
compliant)
PS/2Visa, Mastercard, Personal Check, , , 0, Discover, American Express mouse/keyboard port (Y-connector
supported)
Universal Serial Bus port
ECP parallel port
High speed serial port (16550 UART
compatible)
Port Replicator connector
Headphone jack, Microphone port
RJ-11 port
Composite Video Port 
Preinstalled Operating System
Windows 98SE 
Additional Software
Customizable Toshiba/My Yahoo! Start Page
Microsoft Internet Explorer
McAfee ActiveShield
RingCentralVisa, Mastercard, Personal Check, , , 0, Discover, American Express (Windows 98 Second Edition only)
MediaMatics DVDExpress
Toshiba Custom Utilities
Satellite Series Online Documentation
Toshiba VirtualTech
Toshiba Great Software Offer: With each Satellite notebook, you will receive your choice of two software titles. The software selection includes titles from the following: Lotus. SmartSuite Millennium Edition, productivity, education/reference, creativity and entertainment titles. 
Security
Power-on password (2-level password support)
HDD access password
Main system memory modem and internal
HDD security screws included
Cable lock slot
SecureSleep (Screen Blank)
Keyboard Lock 
Battery
Rechargeable, removable Lithium Ion battery (10.8V, 4,000mAh)
2.5+ hours battery life
Recharge time: 3 hrs unit off, 4-10 hrs unit on
ACPI V1.0 support
Battery life may vary depending on applications, power management settings and features utilized. Recharge time varies
depending on usage. 
Dimensions 
122. x 103. x 17. 
Weight 
7.0 lbs 
Warranty
1 year parts, labor and battery
      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name>okcbuy </seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>American Express, Discover, Internet Escrow, iEscrow, MasterCard, Money Order, Visa
   </payment_types>
   <shipping_info>Buyer Pays Shipping Costs, FedEx, UPS
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $1.00</current_bid>
     <time_left>1 Day, 17 Hrs </time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 1</num_items>
     <num_bids>  0</num_bids>
     <started_at> $1.00</started_at>
     <bid_increment> $0.10</bid_increment>
     <location> Oklahoma City, Oklahoma, United States</location>
     <opened> 11/14/00 7:27:50 AM</opened>
     <closed> 11/29/00 7:27:50 AM</closed>
     <id_num> 291907</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$1.00
       </highest_bid_amount>
       <quantity> 0</quantity>
   </bid_history>
   <item_info>
      <memory> 64MB 100MHz SDRAM expandable to 768MB</memory>
      <hard_drive> 8.4GB 5400RPM Ultra ATA hard drive</hard_drive>
      <cpu> AMD K6-2 500MHz with 3DNow!</cpu>
      <brand> </brand>
      <description> Processor: AMD K6-2 500MHz with 3DNow!
Mother Board: Super Socket 7 w/1MB Cache, 100MHz buss, &amp; 16 bit on-board sound
Memory: 64MB 100MHz SDRAM expandable to 768MB
Graphics Accelerator: ATI Expert 99, 8MB AGP Graphics
Sound: 192XGD Wave Force PCI by Yamaha
Case: 4-bay ATX Mid Tower Easy Access w/removable tray
Keyboard:104 Key PS/2 Style Keyboard
Mouse:2 Button PS/2 Style Mouse
Hard Drive: 8.4GB 5400RPM Ultra ATA hard drive
CD-ROM: 50X CD-ROM Drive
Floppy Drive: Sony 3.5 1.44MB diskette drive
Fax/Modem: Integrated V.90 56K Data/Fax/Voice Modem
Speakers: Labtech LCS-0120 
      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name> bell25</seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>American Express, C.O.D., Discover, Internet Escrow, iEscrow, MasterCard, Money Order, Personal Check, Visa
   </payment_types>
   <shipping_info>Buyer Pays Shipping Costs, FedEx, Other Shipping Service, UPS, USPS
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $650.00</current_bid>
     <time_left> 3 Days, 3 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 1</num_items>
     <num_bids>  0</num_bids>
     <started_at> $650.00</started_at>
     <bid_increment> </bid_increment>
     <location> SulphurSprings, Texas, United States</location>
     <opened> 11/15/00 5:10:41 PM</opened>
     <closed> 11/30/00 5:10:41 PM</closed>
     <id_num> 294559</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$650.00
       </highest_bid_amount>
       <quantity>0 </quantity>
   </bid_history>
   <item_info>
      <memory> 32 mb.</memory>
      <hard_drive> 10.2 gb.</hard_drive>
      <cpu> 500 mhz</cpu>
      <brand> Gateway</brand>
      <description> A nearly new Gateway Essentials 500 mhz. complete system. with windows 98 2nd. edition pre-installed and operating system cd and system restoration cd plus some other software with original cds. and manuals including the windows 98 operating system manual plus other documentation. including a 15 inch color EV500 monitor, 32 mb. of ram , a 10.2 gb. hd. 44x panasonic cdrom , a 56k modem ,pci soundcards and sound blaster video cards . A mic. a 104key internet keyboard. a wheel mouse, altech-lansing speakers, &amp; much more almost new had since April of this year. buyer Must be willing to pay the shipping costs of aprox.55.00 depending on shipper which is the buyers choice . but item will not be shipped until payment is recieved in full. no debit cards or bank drafts please? all other payment options are fine. so if intrested please contact me asap ? or 321gone.com ? and thank you and have a nice day! p.s. it has a intel celeron processor with it Eq. to a pent 3 .
      </description>
   </item_info>
</listing>

                   <listing>
   <seller_info>
       <seller_name> lapro8</seller_name>
       <seller_rating> 0</seller_rating>
   </seller_info>
   <payment_types>Money Order
   </payment_types>
   <shipping_info>International Shipping, See Shipping Description
   </shipping_info>
   <buyer_protection_info>
   </buyer_protection_info>
   <auction_info>
     <current_bid> $320.00</current_bid>
     <time_left> 4 Days, 21 Hrs</time_left>
     <high_bidder> 
        <bidder_name> </bidder_name>
        <bidder_rating> </bidder_rating>
     </high_bidder>
     <num_items> 1</num_items>
     <num_bids>  0</num_bids>
     <started_at> $320.00</started_at>
     <bid_increment> $5.00</bid_increment>
     <location> Cherkasy, Ukraine</location>
     <opened> 11/27/00 11:18:36 AM</opened>
     <closed> 12/2/00 11:18:36 AM</closed>
     <id_num> 320764</id_num>
     <notes>  </notes>
   </auction_info>
   <bid_history>
       <highest_bid_amount>$320.00
       </highest_bid_amount>
       <quantity> 0</quantity>
   </bid_history>
   <item_info>
      <memory> 64 MB of SDRAM</memory>
      <hard_drive> 6.4 GB</hard_drive>
      <cpu> Pentium 300 MHz processor with MMX technology </cpu>
      <brand> VAIO</brand>
      <description> A SuperSlim notebook computer that's light on weight, heavy on features and performance *This .9 thin Notebook Computer weighs in at roughly 3 pounds - which might make you wonder how they cram such great features into that small package *10.4 XGA Active matrix screen with XBRITE display technology *Intel Pentium 300 MHz processor with MMX technology *64 MB of SDRAM is included (expandable to 128 MB maximum) *6.4 GB fixed Hard Drive for Data Storage *Touch Pad with pen operation *One Type II PC card slot with Cardbus Zoomed Video support *External 1.44 MB floppy disk drive *integrated 56K V.90 Data/fax Modem for Internet access *512 KB MultiBank DRAM Cache memory *16-bit, Soundblaster compatible audio *MPEG1 Digital video that supports full screen playback *mono speakers *Built-in microphone *Infrared port *Responsive nearly full-size tactile Keyboard *programmable power key for unattended Email retrieval Please add $30 for shipping. Payment - western union.
      </description>
   </item_info>
</listing>
</root>""")
        print('xml end')
        ret_val = {"dummy_data": ret_str_25KB}
        s = SerWOObject(body=ret_val)
        return s
    except Exception as e:
        print('in xml '+e)
        return None

