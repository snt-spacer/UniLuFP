#include <chrono>
#include <cstring>
#include <fcntl.h>
#include <iostream>
#include <linux/can.h>
#include <linux/can/raw.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <unistd.h>

int main(int argc, char **argv)
{
  const char *ifname = "can0";  // CAN interface name
  const canid_t can_id = 0x104; // CAN ID

  struct sockaddr_can addr;
  struct ifreq ifr;
  struct can_frame frame;

  // Create a socket
  int sock = socket(PF_CAN, SOCK_RAW, CAN_RAW);

  // Set socket non-blocking
  int flags = fcntl(sock, F_GETFL, 0);
  fcntl(sock, F_SETFL, flags | O_NONBLOCK);

  if (sock < 0)
  {
    perror("Error while opening socket");
    return 1;
  }

  std::strcpy(ifr.ifr_name, ifname);
  if (ioctl(sock, SIOCGIFINDEX, &ifr) < 0)
  {
    perror("Error getting interface index");
    return 1;
  }

  addr.can_family = AF_CAN;
  addr.can_ifindex = ifr.ifr_ifindex;

  if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0)
  {
    perror("Error in socket bind");
    return 1;
  }

  // Make a CAN frame
  // Command to power on the motor: ID=0x104, Data=0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFC
  frame.can_id = can_id;
  frame.can_dlc = 8;
  std::memset(frame.data, 0xFF, 7);
  frame.data[7] = 0xFC;

  // Send the CAN frame multiple times
  for (int i = 0; i < 10; i++)
  {
    ssize_t nbytes = write(sock, &frame, sizeof(struct can_frame));
    if (nbytes != sizeof(struct can_frame))
    {
      perror("Error while writing to socket");
      return 1;
    }
  }

  std::cout << "Message sent: 104#FFFFFFFFFFFFFFFC" << std::endl;

  // Receive a CAN frame
  struct can_frame recv_frame;
  ssize_t nbytes = read(sock, &recv_frame, sizeof(struct can_frame));

  // Wait for a CAN frame which has the same ID as the sent frame
  // Set timeout to 3 seconds
  auto start = std::chrono::steady_clock::now();
  std::cout << "Waiting for message..." << std::endl;
  while (recv_frame.can_id != frame.can_id)
  {
    nbytes = read(sock, &recv_frame, sizeof(struct can_frame));
    auto end = std::chrono::steady_clock::now();
    if (std::chrono::duration_cast<std::chrono::seconds>(end - start).count() > 3)
    {
      std::cout << "Timeout: No message received" << std::endl;
      close(sock);
      return 1;
    }
  }

  std::cout << "Message received: " << std::hex << recv_frame.can_id << "#";
  for (int i = 0; i < recv_frame.can_dlc; i++)
  {
    std::cout << std::hex << (int)recv_frame.data[i];
  }
  std::cout << std::endl;

  close(sock);
  return 0;
}